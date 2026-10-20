import csv
import glob
import os

from pipeline import load_image, find_pair, detect_changes
from eval_utils import STATIC, reference, get_gt, metrics

SWEEPS = {
    "threshold": [None, 10, 20, 30, 40, 60, 80, 100],   # None = Otsu
    "min_area": [0, 50, 100, 200, 500, 1000, 2000],
    "blur": [1, 3, 5, 7, 9, 11],
}
BASE = dict(method="diff", align=True)    # alignment falls back automatically if it fails

names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})
rows = []
for name in names:
    if name in STATIC:
        continue
    b, a = find_pair(name)
    before, after = load_image(b), load_image(a)
    roi, shape, aligned, overlap = reference(before, after)
    gt, kind = get_gt(name, shape)
    if gt is None:
        continue
    for param, values in SWEEPS.items():
        for v in values:
            settings = {**BASE, param: v}
            r = detect_changes(before, after, **settings)
            m = metrics(r["mask_final"] > 0, gt, roi)
            rows.append([name, param, "otsu" if v is None else v,
                         f"{m['f1']:.4f}", f"{m['precision']:.4f}",
                         f"{m['recall']:.4f}", f"{m['iou']:.4f}",
                         f"{m['pred_percent']:.3f}"])
    print("done:", name)

os.makedirs("outputs", exist_ok=True)
with open("outputs/sweep_f1.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["pair", "param", "value", "f1", "precision", "recall", "iou", "pred_percent"])
    w.writerows(rows)
print("Saved outputs/sweep_f1.csv")