import csv
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pipeline import load_image, find_pair, detect_changes

DEFAULTS = dict(blur=5, threshold=None, morph_kernel=5, min_area=200)
SWEEPS = {
    "blur": [1, 3, 5, 7, 9, 11],
    "min_area": [0, 50, 100, 200, 500, 1000, 2000],
    "threshold": [None, 10, 20, 30, 40, 60, 80, 100],   # None = Otsu
}
TARGET = "nochange"   # false-positive test pair

names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})
if TARGET not in names:
    print(f"Warning: '{TARGET}' pair not found, using {names[0]} instead")
    TARGET = names[0]

rows = []
curves = {}   # (method, param) -> list of (value, change %, regions)

for name in names:
    b, a = find_pair(name)
    before, after = load_image(b), load_image(a)
    for method in ("diff", "ssim"):
        for param, values in SWEEPS.items():
            for v in values:
                settings = {**DEFAULTS, param: v}
                s = detect_changes(before, after, method=method, **settings)["stats"]
                rows.append([name, method, param, "otsu" if v is None else v,
                             round(s["change_percent"], 3), s["regions"]])
                if name == TARGET:
                    curves.setdefault((method, param), []).append(
                        (v, s["change_percent"], s["regions"]))
    print("done:", name)

os.makedirs("outputs", exist_ok=True)
with open("outputs/sweep_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair", "method", "param", "value", "change_percent", "regions"])
    w.writerows(rows)

# Draft plot: three panels on the target pair
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3))
panels = [("blur", 1, "Gaussian kernel size", "Change (%)"),
          ("min_area", 2, "Minimum area (px)", "Regions"),
          ("threshold", 1, "Threshold", "Change (%)")]
for ax, (param, idx, xlabel, ylabel) in zip(axes, panels):
    for method, style in (("diff", "o-"), ("ssim", "s--")):
        pts = curves[(method, param)]
        labels = ["Otsu" if p[0] is None else str(p[0]) for p in pts]
        ax.plot(range(len(pts)), [p[idx] for p in pts], style, label=method)
        ax.set_xticks(range(len(pts)))
        ax.set_xticklabels(labels)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
axes[0].legend()
fig.suptitle(f"Draft sensitivity on '{TARGET}' (no ground truth yet)", fontsize=9)
fig.tight_layout()
fig.savefig("outputs/fig9_draft_sensitivity.png", dpi=300)
print("Saved outputs/sweep_results.csv and outputs/fig9_draft_sensitivity.png")