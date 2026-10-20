import os

import cv2
import numpy as np

from pipeline import detect_changes

GT_DIR = "../ground_truth"
# Scenes with NO intended change. Remove a name here if you find an object moved in it.
STATIC = {"nochange", "shiftstatic", "lightstatic"}

VARIANTS = [
    ("V1_diff",             dict(method="diff")),
    ("V2_ssim",             dict(method="ssim")),
    ("V3_diff_align",       dict(method="diff", align=True)),
    ("V4_diff_clahe",       dict(method="diff", normalize="clahe")),
    ("V5_diff_match",       dict(method="diff", normalize="match")),
    ("V6_diff_align_clahe", dict(method="diff", align=True, normalize="clahe")),
    ("V7_diff_align_match", dict(method="diff", align=True, normalize="match")),
    ("V8_ssim_align",       dict(method="ssim", align=True)),
]


def reference(before, after):
    """Common evaluation region: the overlap area if alignment works, else the whole frame."""
    ref = detect_changes(before, after, method="diff", align=True)
    shape = ref["before"].shape[:2]
    aligned = ref["stats"]["aligned"]
    roi = (ref["valid"] > 0) if aligned else np.ones(shape, bool)
    return roi, shape, aligned, ref["stats"]["valid_percent"]


def get_gt(name, shape):
    """Return (ground-truth mask as bool, kind) or (None, None) if missing."""
    if name in STATIC:
        return np.zeros(shape, bool), "static"
    path = os.path.join(GT_DIR, f"{name}_gt.png")
    if not os.path.exists(path):
        return None, None
    gt = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if gt is None:
        raise SystemExit(f"Could not read {path}")
    if gt.shape != shape:
        raise SystemExit(
            f"{path} is {gt.shape[1]}x{gt.shape[0]}, but the processed image is "
            f"{shape[1]}x{shape[0]}. Export at the exact size of templates/{name}_before.png")
    return gt > 127, "annotated"


def metrics(pred, gt, roi):
    p, g = pred & roi, gt & roi
    tp = int(np.sum(p & g))
    fp = int(np.sum(p & ~g))
    fn = int(np.sum(~p & g))
    n = int(roi.sum())
    nan = float("nan")
    return {
        "tp": tp, "fp": fp, "fn": fn, "roi_pixels": n,
        "precision": tp / (tp + fp) if tp + fp else nan,
        "recall": tp / (tp + fn) if tp + fn else nan,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else nan,
        "iou": tp / (tp + fp + fn) if tp + fp + fn else nan,
        "pred_percent": 100 * (tp + fp) / n if n else nan,
        "gt_percent": 100 * (tp + fn) / n if n else nan,
    }