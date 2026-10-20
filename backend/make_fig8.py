import os

import cv2
import numpy as np

from pipeline import load_image, find_pair, detect_changes
from eval_utils import reference, get_gt, metrics

ROWS = ["pair1", "lightobj", "pair3" ,"shiftobj"]          # edit: your annotated pairs
BASELINE = dict(method="diff")
FINAL = dict(method="diff", align=True)
W = 300


def tile(img, text):
    h, w = img.shape[:2]
    img = cv2.resize(img, (W, int(h * W / w)))
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for color, thick in (((0, 0, 0), 3), ((255, 255, 255), 1)):
        cv2.putText(img, text, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thick, cv2.LINE_AA)
    return img


def coloured(pred, gt, roi):
    out = np.full(pred.shape + (3,), 40, np.uint8)       # dark grey outside the evaluated area
    out[roi] = 0
    out[roi & pred & gt] = (0, 200, 0)                   # true positive: green
    out[roi & pred & ~gt] = (0, 0, 255)                  # false positive: red
    out[roi & ~pred & gt] = (255, 0, 0)                  # false negative: blue
    return out


rows = []
for name in ROWS:
    b, a = find_pair(name)
    before, after = load_image(b), load_image(a)
    roi, shape, aligned, overlap = reference(before, after)
    gt, kind = get_gt(name, shape)
    ref = detect_changes(before, after, method="diff", align=True)
    after_view = ref["after_aligned"] if ref["after_aligned"] is not None else ref["after"]
    tiles = [tile(ref["before"], f"{name} before"), tile(after_view, "after"),
             tile((gt * 255).astype(np.uint8), "ground truth")]
    for label, settings in (("baseline", BASELINE), ("final", FINAL)):
        r = detect_changes(before, after, **settings)
        pred = r["mask_final"] > 0
        m = metrics(pred, gt, roi)
        tiles.append(tile(coloured(pred, gt, roi), f"{label} F1={m['f1']:.2f}"))
    height = min(t.shape[0] for t in tiles)
    rows.append(np.hstack([t[:height] for t in tiles]))

width = max(r.shape[1] for r in rows)
rows = [cv2.copyMakeBorder(r, 0, 0, 0, width - r.shape[1], cv2.BORDER_CONSTANT) for r in rows]
os.makedirs("outputs", exist_ok=True)
cv2.imwrite("outputs/fig8_qualitative.png", np.vstack(rows))
print("Saved outputs/fig8_qualitative.png (green = TP, red = FP, blue = FN)")