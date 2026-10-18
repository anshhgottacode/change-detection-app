"""Change detection pipeline (Day 2)."""
import os
import time

import cv2
import numpy as np
from skimage.metrics import structural_similarity


def load_image(path):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img


def find_pair(name, folder="../test_images"):
    """Find <name>_before.* and <name>_after.* in the folder."""
    paths = []
    for role in ("before", "after"):
        match = None
        for ext in ("jpg", "jpeg", "png", "JPG", "JPEG", "PNG"):
            candidate = os.path.join(folder, f"{name}_{role}.{ext}")
            if os.path.exists(candidate):
                match = candidate
                break
        if match is None:
            raise FileNotFoundError(f"No {name}_{role} image found in {folder}")
        paths.append(match)
    return paths


def match_sizes(before, after, max_width=1280):
    """Resize 'after' to match 'before', then shrink both if too wide (speed)."""
    after = cv2.resize(after, (before.shape[1], before.shape[0]))
    h, w = before.shape[:2]
    if w > max_width:
        scale = max_width / w
        size = (max_width, int(h * scale))
        before = cv2.resize(before, size, interpolation=cv2.INTER_AREA)
        after = cv2.resize(after, size, interpolation=cv2.INTER_AREA)
    return before, after


def to_gray(img, blur):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if blur > 1:
        if blur % 2 == 0:      # Gaussian kernel size must be odd
            blur += 1
        gray = cv2.GaussianBlur(gray, (blur, blur), 0)
    return gray


def compute_change_map(g1, g2, method):
    """Return a uint8 map where larger values mean more change."""
    if method == "diff":
        return cv2.absdiff(g1, g2)
    if method == "ssim":
        _, ssim_map = structural_similarity(g1, g2, full=True, data_range=255)
        return np.clip((1.0 - ssim_map) * 255, 0, 255).astype(np.uint8)
    raise ValueError("method must be 'diff' or 'ssim'")


def detect_changes(before, after, method="ssim", blur=5, threshold=None,
                   morph_kernel=5, min_area=200, max_width=1280):
    """Run the full pipeline. threshold=None means automatic Otsu threshold."""
    clock = time.perf_counter
    timings = {}

    # 1. Preprocess
    t = clock()
    before, after = match_sizes(before, after, max_width)
    g1, g2 = to_gray(before, blur), to_gray(after, blur)
    timings["preprocess_ms"] = (clock() - t) * 1000

    # 2. Change map (difference or SSIM)
    t = clock()
    change_map = compute_change_map(g1, g2, method)
    timings["change_map_ms"] = (clock() - t) * 1000

    # 3. Threshold
    t = clock()
    if threshold is None:
        used, raw = cv2.threshold(change_map, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        used, raw = cv2.threshold(change_map, threshold, 255, cv2.THRESH_BINARY)
    timings["threshold_ms"] = (clock() - t) * 1000

    # 4. Post-process: morphology, then keep only regions >= min_area
    t = clock()
    kernel = np.ones((morph_kernel, morph_kernel), np.uint8)
    clean = cv2.morphologyEx(raw, cv2.MORPH_OPEN, kernel)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    kept = [c for c in contours if cv2.contourArea(c) >= min_area]

    final = np.zeros_like(clean)
    cv2.drawContours(final, kept, -1, 255, thickness=cv2.FILLED)

    overlay = after.copy()
    for c in kept:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
    timings["postprocess_ms"] = (clock() - t) * 1000

    # 5. Outputs and statistics (percentage now uses the FINAL mask)
    norm = cv2.normalize(change_map, None, 0, 255, cv2.NORM_MINMAX)
    heatmap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)

    stats = {
        "change_percent": 100.0 * np.count_nonzero(final) / final.size,
        "regions": len(kept),
        "threshold": float(used),
        "width": before.shape[1],
        "height": before.shape[0],
        **timings,
        "total_ms": sum(timings.values()),
    }
    return {
        "before": before, "after": after,
        "change_map": change_map, "mask_raw": raw, "mask_clean": clean,
        "mask_final": final, "heatmap": heatmap, "overlay": overlay,
        "stats": stats,
    }


def save_outputs(result, folder):
    os.makedirs(folder, exist_ok=True)
    names = {
        "before": "0_before.png", "after": "0_after.png",
        "change_map": "1_change_map.png", "mask_raw": "2_mask_raw.png",
        "mask_clean": "3_mask_clean.png", "mask_final": "4_mask_final.png",
        "heatmap": "5_heatmap.png", "overlay": "6_overlay_boxes.png",
    }
    for key, filename in names.items():
        cv2.imwrite(os.path.join(folder, filename), result[key])