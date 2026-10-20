import csv
import glob
import os
import warnings

import numpy as np

from pipeline import load_image, find_pair, detect_changes
from eval_utils import STATIC, VARIANTS, reference, get_gt, metrics

warnings.filterwarnings("ignore", category=RuntimeWarning)
names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})
print("Assumed static (no change):", sorted(STATIC & set(names)))


def f(v):
    return "  n/a" if v != v else f"{v:5.3f}"


rows = []
print(f"\n{'pair':<12}{'variant':<22}{'kind':<10}{'prec':>6}{'rec':>6}{'F1':>6}{'IoU':>6}{'pred%':>7}")
for name in names:
    b, a = find_pair(name)
    before, after = load_image(b), load_image(a)
    roi, shape, aligned, overlap = reference(before, after)
    gt, kind = get_gt(name, shape)
    if gt is None:
        print(f"{name:<12} skipped: no ground truth (ground_truth/{name}_gt.png)")
        continue
    for variant, settings in VARIANTS:
        r = detect_changes(before, after, **settings)
        m = metrics(r["mask_final"] > 0, gt, roi)
        rows.append([name, kind, variant, r["stats"]["aligned"],
                     round(100 * roi.mean(), 2), m["tp"], m["fp"], m["fn"],
                     f"{m['precision']:.4f}", f"{m['recall']:.4f}",
                     f"{m['f1']:.4f}", f"{m['iou']:.4f}",
                     f"{m['pred_percent']:.3f}", f"{m['gt_percent']:.3f}",
                     r["stats"]["regions"]])
        print(f"{name:<12}{variant:<22}{kind:<10}{f(m['precision']):>6}"
              f"{f(m['recall']):>6}{f(m['f1']):>6}{f(m['iou']):>6}"
              f"{m['pred_percent']:>7.2f}")

os.makedirs("outputs", exist_ok=True)
header = ["pair", "kind", "variant", "variant_aligned", "roi_percent", "tp", "fp",
          "fn", "precision", "recall", "f1", "iou", "pred_percent", "gt_percent",
          "regions"]
with open("outputs/results_day6.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(header)
    w.writerows(rows)

# Summary per variant
print("\nSummary (descriptive; few pairs, so read per-pair rows first)")
print(f"{'variant':<22}{'n annot':>8}{'mean F1':>9}{'mean IoU':>10}{'n static':>9}{'mean false %':>13}")
summary = []
for variant, _ in VARIANTS:
    ann = [r for r in rows if r[2] == variant and r[1] == "annotated"]
    sta = [r for r in rows if r[2] == variant and r[1] == "static"]
    f1 = np.nanmean([float(r[10]) for r in ann]) if ann else float("nan")
    iou = np.nanmean([float(r[11]) for r in ann]) if ann else float("nan")
    fp = np.mean([float(r[12]) for r in sta]) if sta else float("nan")
    summary.append([variant, len(ann), f"{f1:.4f}", f"{iou:.4f}", len(sta), f"{fp:.3f}"])
    print(f"{variant:<22}{len(ann):>8}{f1:>9.3f}{iou:>10.3f}{len(sta):>9}{fp:>13.2f}")
with open("outputs/summary_day6.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["variant", "n_annotated", "mean_f1", "mean_iou", "n_static", "mean_false_change_percent"])
    w.writerows(summary)
print("\nSaved outputs/results_day6.csv and outputs/summary_day6.csv")