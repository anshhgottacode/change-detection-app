"""Change detection pipeline (Day 3: alignment + illumination normalisation)."""
import os
import time

import cv2
import numpy as np
from skimage.exposure import match_histograms
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


def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def blur_gray(gray, blur):
    if blur > 1:
        if blur % 2 == 0:      # Gaussian kernel size must be odd
            blur += 1
        gray = cv2.GaussianBlur(gray, (blur, blur), 0)
    return gray


def normalise_illumination(g1, g2, mode):
    """mode: None, 'clahe' or 'match'. Returns the two grayscale images."""
    if mode is None:
        return g1, g2
    if mode == "clahe":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(g1), clahe.apply(g2)
    if mode == "match":
        matched = match_histograms(g2, g1)
        return g1, np.clip(matched, 0, 255).astype(np.uint8)
    raise ValueError("normalize must be None, 'clahe' or 'match'")


def align_images(before, after, nfeatures=3000, ratio=0.75,
                 ransac_thresh=4.0, min_inliers=15):
    """Warp 'after' onto 'before' with ORB features and a RANSAC homography.

    Returns (aligned_after, valid_mask, match_picture, info).
    If alignment fails, returns the unchanged 'after' with info['aligned'] False.
    """
    info = {"aligned": False, "keypoints_before": 0, "keypoints_after": 0,
            "matches": 0, "inliers": 0, "reason": ""}
    g1, g2 = to_gray(before), to_gray(after)

    orb = cv2.ORB_create(nfeatures=nfeatures)
    k1, d1 = orb.detectAndCompute(g1, None)
    k2, d2 = orb.detectAndCompute(g2, None)
    info["keypoints_before"], info["keypoints_after"] = len(k1), len(k2)
    if d1 is None or d2 is None or len(k1) < min_inliers or len(k2) < min_inliers:
        info["reason"] = "too few keypoints"
        return after, None, None, info

    # Match 'after' descriptors to 'before' descriptors, keep clearly good matches
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(d2, d1, k=2)
    good = [p[0] for p in pairs
            if len(p) == 2 and p[0].distance < ratio * p[1].distance]
    info["matches"] = len(good)
    if len(good) < min_inliers:
        info["reason"] = "too few good matches"
        return after, None, None, info

    src = np.float32([k2[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([k1[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, ransac_thresh)
    if H is None or mask is None:
        info["reason"] = "homography failed"
        return after, None, None, info

    inliers = int(mask.sum())
    info["inliers"] = inliers
    if inliers < min_inliers:
        info["reason"] = "too few inliers"
        return after, None, None, info

    det = float(np.linalg.det(H[:2, :2]))
    if not (0.5 < det < 2.0):
        info["reason"] = f"implausible warp (det={det:.2f})"
        return after, None, None, info

    h, w = before.shape[:2]
    aligned = cv2.warpPerspective(after, H, (w, h))

    # Pixels that exist in the warped image (the rest is black border)
    valid = cv2.warpPerspective(np.full(after.shape[:2], 255, np.uint8), H, (w, h))
    valid = cv2.erode(valid, np.ones((15, 15), np.uint8))
    valid = cv2.threshold(valid, 250, 255, cv2.THRESH_BINARY)[1]

    # Picture of up to 60 inlier matches (before on the left, after on the right)
    inl = [m for m, keep in zip(good, mask.ravel()) if keep][:60]
    swapped = [cv2.DMatch(m.trainIdx, m.queryIdx, 0, m.distance) for m in inl]
    vis = cv2.drawMatches(before, k1, after, k2, swapped, None,
                          flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    info["aligned"] = True
    return aligned, valid, vis, info


def compute_change_map(g1, g2, method):
    """Return a uint8 map where larger values mean more change."""
    if method == "diff":
        return cv2.absdiff(g1, g2)
    if method == "ssim":
        _, ssim_map = structural_similarity(g1, g2, full=True, data_range=255)
        return np.clip((1.0 - ssim_map) * 255, 0, 255).astype(np.uint8)
    raise ValueError("method must be 'diff' or 'ssim'")


def detect_changes(before, after, method="ssim", blur=5, threshold=None,
                   morph_kernel=5, min_area=200, max_width=1280,
                   align=False, normalize=None, orb_features=3000,
                   ratio=0.75, ransac_thresh=4.0, min_inliers=15):
    """Run the full pipeline. threshold=None means automatic Otsu threshold."""
    clock = time.perf_counter
    timings = {"align_ms": 0.0}

    before, after = match_sizes(before, after, max_width)
    blend_raw = cv2.addWeighted(before, 0.5, after, 0.5, 0)

    # 0. Optional alignment
    valid, match_pic, aligned_img, blend_aligned = None, None, None, None
    ainfo = {"aligned": False, "keypoints_before": 0, "keypoints_after": 0,
             "matches": 0, "inliers": 0,
             "reason": "not requested" if not align else ""}
    after_used = after
    if align:
        t = clock()
        aligned_img, valid, match_pic, ainfo = align_images(
            before, after, orb_features, ratio, ransac_thresh, min_inliers)
        timings["align_ms"] = (clock() - t) * 1000
        if ainfo["aligned"]:
            after_used = aligned_img
            blend_aligned = cv2.addWeighted(before, 0.5, aligned_img, 0.5, 0)
        else:
            aligned_img, valid = None, None   # fall back to the plain resized image

    # 1. Preprocess: grayscale, illumination normalisation, blur
    t = clock()
    g1, g2 = to_gray(before), to_gray(after_used)
    g1, g2 = normalise_illumination(g1, g2, normalize)
    g1, g2 = blur_gray(g1, blur), blur_gray(g2, blur)
    timings["preprocess_ms"] = (clock() - t) * 1000

    # 2. Change map (difference or SSIM)
    t = clock()
    change_map = compute_change_map(g1, g2, method)
    timings["change_map_ms"] = (clock() - t) * 1000

    # 3. Threshold (Otsu is computed only on valid pixels when aligned)
    t = clock()
    if valid is not None and np.count_nonzero(valid) > 0:
        if threshold is None:
            vals = change_map[valid > 0].reshape(-1, 1)
            used, _ = cv2.threshold(vals, 0, 255,
                                    cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            used = threshold
        _, raw = cv2.threshold(change_map, used, 255, cv2.THRESH_BINARY)
        raw[valid == 0] = 0
    elif threshold is None:
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

    overlay = after_used.copy()
    for c in kept:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
    timings["postprocess_ms"] = (clock() - t) * 1000

    # 5. Outputs and statistics (percentage is over valid pixels when aligned)
    norm = cv2.normalize(change_map, None, 0, 255, cv2.NORM_MINMAX)
    heatmap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    area = np.count_nonzero(valid) if valid is not None else final.size

    stats = {
        "change_percent": 100.0 * np.count_nonzero(final) / area,
        "regions": len(kept),
        "threshold": float(used),
        "width": before.shape[1],
        "height": before.shape[0],
        "aligned": ainfo["aligned"],
        "align_reason": ainfo["reason"],
        "keypoints_before": ainfo["keypoints_before"],
        "keypoints_after": ainfo["keypoints_after"],
        "matches": ainfo["matches"],
        "inliers": ainfo["inliers"],
        "valid_percent": 100.0 * area / final.size,
        **timings,
        "total_ms": sum(timings.values()),
    }
    return {
        "before": before, "after": after, "after_aligned": aligned_img,
        "change_map": change_map, "mask_raw": raw, "mask_clean": clean,
        "mask_final": final, "heatmap": heatmap, "overlay": overlay,
        "matches": match_pic, "blend_raw": blend_raw,
        "blend_aligned": blend_aligned, "valid": valid, "stats": stats,
    }


def save_outputs(result, folder):
    os.makedirs(folder, exist_ok=True)
    names = {
        "before": "0_before.png", "after": "0_after.png",
        "after_aligned": "0_after_aligned.png",
        "change_map": "1_change_map.png", "mask_raw": "2_mask_raw.png",
        "mask_clean": "3_mask_clean.png", "mask_final": "4_mask_final.png",
        "heatmap": "5_heatmap.png", "overlay": "6_overlay_boxes.png",
        "matches": "7_matches.png", "blend_raw": "8_blend_raw.png",
        "blend_aligned": "8_blend_aligned.png", "valid": "9_valid_mask.png",
    }
    for key, filename in names.items():
        if result.get(key) is not None:      # skip outputs that do not exist
            cv2.imwrite(os.path.join(folder, filename), result[key])