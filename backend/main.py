"""FastAPI backend for the change detection app (Day 4)."""
import base64
import io
import logging
import os
import time
from typing import Literal, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from pipeline import detect_changes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("change-detection")

# Limits (can be overridden with environment variables when deployed)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_PIXELS = int(os.getenv("MAX_PIXELS", str(40_000_000)))
MAX_WIDTH_CAP = int(os.getenv("MAX_WIDTH_CAP", "1920"))
MIN_SIDE = 32
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
           if o.strip()]

app = FastAPI(title="Change Detection API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def read_image(upload: UploadFile, label: str):
    """Validate an uploaded file and decode it to a BGR image."""
    limit = MAX_UPLOAD_MB * 1024 * 1024
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"{label} image is larger than {MAX_UPLOAD_MB} MB.")
    if not data:
        raise HTTPException(400, f"{label} image is empty.")

    # Check the real file content, not the file name or declared type
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt, (w, h) = im.format, im.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, f"{label} file is not a valid image.") from None
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(415, f"{label} image must be JPEG, PNG or WebP (got {fmt}).")
    if w * h > MAX_PIXELS:
        raise HTTPException(413, f"{label} image has too many pixels (limit {MAX_PIXELS:,}).")
    if min(w, h) < MIN_SIDE:
        raise HTTPException(400, f"{label} image must be at least {MIN_SIDE}x{MIN_SIDE} px.")

    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, f"{label} image could not be decoded.")
    return img


def to_data_uri(img, fmt="jpg"):
    """Encode an image as a base64 data URI (PNG for masks, JPEG otherwise)."""
    if fmt == "png":
        ok, buf = cv2.imencode(".png", img)
        mime = "image/png"
    else:
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        mime = "image/jpeg"
    if not ok:
        raise HTTPException(500, "Could not encode a result image.")
    return f"data:{mime};base64," + base64.b64encode(buf.tobytes()).decode("ascii")


@app.get("/")
def root():
    return {"name": "Change Detection API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/config")
def config():
    """Limits and options, so the frontend can build its controls from them."""
    return {
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_width_cap": MAX_WIDTH_CAP,
        "methods": ["diff", "ssim"],
        "normalize": ["none", "clahe", "match"],
        "defaults": {"method": "diff", "blur": 5, "threshold": None,
                     "morph_kernel": 5, "min_area": 200, "max_width": 1280,
                     "align": False, "normalize": "none"},
    }


@app.post("/analyze")
async def analyze(
    before: UploadFile = File(...),
    after: UploadFile = File(...),
    method: Literal["diff", "ssim"] = Form("diff"),
    blur: int = Form(5, ge=1, le=21),
    threshold: Optional[str] = Form(None),
    morph_kernel: int = Form(5, ge=1, le=31),
    min_area: int = Form(200, ge=0, le=1_000_000),
    max_width: int = Form(1280, ge=320, le=MAX_WIDTH_CAP),
    align: bool = Form(False),
    normalize: Literal["none", "clahe", "match"] = Form("none"),
):
    t0 = time.perf_counter()

    # threshold: empty means automatic (Otsu)
    thr = None
    if threshold not in (None, "", "auto"):
        try:
            thr = int(threshold)
        except ValueError:
            raise HTTPException(422, "threshold must be an integer 0-255, or empty for Otsu.") from None
        if not 0 <= thr <= 255:
            raise HTTPException(422, "threshold must be between 0 and 255.")

    img1 = await read_image(before, "Before")
    img2 = await read_image(after, "After")
    t_decoded = time.perf_counter()

    try:
        result = await run_in_threadpool(
            detect_changes, img1, img2,
            method=method, blur=blur, threshold=thr, morph_kernel=morph_kernel,
            min_area=min_area, max_width=max_width, align=align,
            normalize=None if normalize == "none" else normalize,
        )
    except Exception:
        log.exception("Pipeline failed")
        raise HTTPException(500, "Processing failed. Try different images or settings.") from None
    t_processed = time.perf_counter()

    s = result["stats"]
    after_img = result["after_aligned"] if result["after_aligned"] is not None else result["after"]
    images = {
        "before": to_data_uri(result["before"]),
        "after": to_data_uri(after_img),
        "heatmap": to_data_uri(result["heatmap"]),
        "mask": to_data_uri(result["mask_final"], "png"),
        "overlay": to_data_uri(result["overlay"]),
    }
    if s["aligned"]:
        images["blend_raw"] = to_data_uri(result["blend_raw"])
        images["blend_aligned"] = to_data_uri(result["blend_aligned"])
        images["matches"] = to_data_uri(result["matches"])
    t_encoded = time.perf_counter()

    stats = {
        "change_percent": round(s["change_percent"], 3),
        "regions": int(s["regions"]),
        "threshold": round(float(s["threshold"]), 1),
        "width": int(s["width"]),
        "height": int(s["height"]),
        "aligned": bool(s["aligned"]),
        "alignment_note": s["align_reason"] if align and not s["aligned"] else "",
        "keypoints_before": int(s["keypoints_before"]),
        "keypoints_after": int(s["keypoints_after"]),
        "matches": int(s["matches"]),
        "inliers": int(s["inliers"]),
        "valid_percent": round(s["valid_percent"], 2),
    }
    timing = {k: round(float(s[k]), 1) for k in
              ("preprocess_ms", "align_ms", "change_map_ms",
               "threshold_ms", "postprocess_ms")}
    timing["pipeline_ms"] = round(float(s["total_ms"]), 1)
    timing["decode_ms"] = round((t_decoded - t0) * 1000, 1)
    timing["encode_ms"] = round((t_encoded - t_processed) * 1000, 1)
    timing["request_ms"] = round((t_encoded - t0) * 1000, 1)

    log.info("analyze %s align=%s norm=%s -> %.2f%% in %.0f ms",
             method, align, normalize, stats["change_percent"], timing["request_ms"])

    return {
        "stats": stats,
        "timing": timing,
        "settings": {"method": method, "blur": blur, "threshold": thr,
                     "morph_kernel": morph_kernel, "min_area": min_area,
                     "max_width": max_width, "align": align,
                     "normalize": normalize},
        "images": images,
    }