import csv
import glob
import os

from pipeline import load_image, find_pair, detect_changes, save_outputs

VARIANTS = [
    ("V1_diff",            dict(method="diff")),
    ("V2_ssim",            dict(method="ssim")),
    ("V3_diff_align",      dict(method="diff", align=True)),
    ("V4_diff_clahe",      dict(method="diff", normalize="clahe")),
    ("V5_diff_match",      dict(method="diff", normalize="match")),
    ("V6_diff_align_clahe", dict(method="diff", align=True, normalize="clahe")),
    ("V7_diff_align_match", dict(method="diff", align=True, normalize="match")),
    ("V8_ssim_align",      dict(method="ssim", align=True)),
]

names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})
rows = []
print(f"{'pair':<12}{'variant':<22}{'change %':>9}{'regions':>9}{'aligned':>9}"
      f"{'inliers':>9}{'ms':>8}")

for name in names:
    b, a = find_pair(name)
    before, after = load_image(b), load_image(a)
    for variant, settings in VARIANTS:
        result = detect_changes(before, after, **settings)
        save_outputs(result, os.path.join("outputs", name, variant))
        s = result["stats"]
        rows.append([name, variant, f"{s['width']}x{s['height']}",
                     round(s["change_percent"], 3), s["regions"],
                     round(s["threshold"]), s["aligned"], s["inliers"],
                     s["matches"], s["align_reason"],
                     round(s["align_ms"], 1), round(s["total_ms"], 1)])
        print(f"{name:<12}{variant:<22}{s['change_percent']:>9.2f}"
              f"{s['regions']:>9}{str(s['aligned']):>9}{s['inliers']:>9}"
              f"{s['total_ms']:>8.0f}")

os.makedirs("outputs", exist_ok=True)
with open("outputs/ablation_day3.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair", "variant", "size", "change_percent", "regions",
                "otsu_threshold", "aligned", "inliers", "matches",
                "align_reason", "align_ms", "total_ms"])
    w.writerows(rows)
print("Saved outputs/ablation_day3.csv")