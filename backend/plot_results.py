import csv
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)
OUT, DPI = "outputs", 300
BAR_VARIANTS = ["V1_diff", "V2_ssim", "V3_diff_align", "V6_diff_align_clahe", "V8_ssim_align"]
LABELS = {"V1_diff": "Diff", "V2_ssim": "SSIM", "V3_diff_align": "Diff+align",
          "V6_diff_align_clahe": "Diff+align+CLAHE", "V8_ssim_align": "SSIM+align"}


def read(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(x):
    try:
        return float(x)
    except ValueError:
        return float("nan")


# ---- Fig. 10(a): F1 per variant and pair ----
res = [r for r in read(f"{OUT}/results_day6.csv") if r["kind"] == "annotated"]
pairs = sorted({r["pair"] for r in res})
f1 = {(r["pair"], r["variant"]): num(r["f1"]) for r in res}
groups = pairs + ["Mean"]
bw = 0.8 / len(BAR_VARIANTS)
fig, ax = plt.subplots(figsize=(7.0, 2.8))
for j, v in enumerate(BAR_VARIANTS):
    vals = [f1.get((p, v), np.nan) for p in pairs]
    vals.append(np.nanmean(vals))
    ax.bar(np.arange(len(groups)) - 0.4 + bw / 2 + j * bw, vals, bw, label=LABELS[v])
ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups)
ax.set_ylabel("F1")
ax.set_ylim(0, 1)
ax.grid(axis="y", alpha=0.3)
ax.legend(fontsize=7, ncol=3)
fig.tight_layout()
fig.savefig(f"{OUT}/fig10a_ablation_f1.png", dpi=DPI)

# ---- Fig. 10(b): stacked runtime per stage (from the Day 4 benchmark) ----
bench = read(f"{OUT}/benchmark_day4.csv")
STAGES = [("preprocess_ms_mean", "Preprocess"), ("align_ms_mean", "Align"),
          ("change_map_ms_mean", "Change map"), ("threshold_ms_mean", "Threshold"),
          ("postprocess_ms_mean", "Post-process")]
CONFIGS = ["diff_align", "ssim_align"]
widths = sorted({int(r["actual_width"]) for r in bench})
fig, ax = plt.subplots(figsize=(7.0, 2.8))
bar = 0.35
for k, cfg in enumerate(CONFIGS):
    x = np.arange(len(widths)) + (k - 0.5) * bar
    sel = [next(r for r in bench if r["config"] == cfg and int(r["actual_width"]) == w) for w in widths]
    bottom = np.zeros(len(widths))
    for i, (key, name) in enumerate(STAGES):
        vals = np.array([num(r[key]) for r in sel])
        ax.bar(x, vals, bar, bottom=bottom, color=f"C{i}", label=name if k == 0 else None)
        bottom += vals
    stds = [num(r["pipeline_ms_std"]) for r in sel]
    ax.errorbar(x, bottom, yerr=stds, fmt="none", ecolor="black", capsize=2)
    for xi, top in zip(x, bottom):
        ax.text(xi, top * 1.02 + 3, cfg.replace("_", "+"), ha="center", fontsize=6)
ax.set_xticks(range(len(widths)))
ax.set_xticklabels([f"{w} px" for w in widths])
ax.set_xlabel("Processing width")
ax.set_ylabel("Time (ms)")
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(f"{OUT}/fig10b_runtime_stacked.png", dpi=DPI)

# ---- Fig. 9: F1 sensitivity ----
sw = read(f"{OUT}/sweep_f1.csv")
PARAMS = [("threshold", "Threshold"), ("min_area", "Minimum area (px)"), ("blur", "Gaussian kernel size")]
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4), sharey=True)
for ax, (param, xlabel) in zip(axes, PARAMS):
    rows = [r for r in sw if r["param"] == param]
    values = list(dict.fromkeys(r["value"] for r in rows))
    ys = []
    for p in sorted({r["pair"] for r in rows}):
        y = [num(next(r["f1"] for r in rows if r["pair"] == p and r["value"] == v)) for v in values]
        ys.append(y)
        ax.plot(range(len(values)), y, "o-", lw=1, ms=3, alpha=0.7, label=p)
    ax.plot(range(len(values)), np.nanmean(ys, axis=0), "k-", lw=2, label="Mean")
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(values, fontsize=7)
    ax.set_xlabel(xlabel)
    ax.grid(alpha=0.3)
axes[0].set_ylabel("F1")
axes[0].set_ylim(0, 1)
axes[0].legend(fontsize=6)
fig.tight_layout()
fig.savefig(f"{OUT}/fig9_sensitivity.png", dpi=DPI)
print("Saved fig9_sensitivity.png, fig10a_ablation_f1.png, fig10b_runtime_stacked.png in outputs/")