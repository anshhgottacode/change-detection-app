import csv
import glob
import os

from pipeline import load_image, find_pair, detect_changes, save_outputs

names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})
if not names:
    raise SystemExit("No *_before.* images found in ../test_images")

os.makedirs("outputs", exist_ok=True)
rows = []
print(f"{'pair':<12}{'method':<7}{'change %':>9}{'regions':>9}{'thr':>6}{'ms':>8}")

for name in names:
    before_path, after_path = find_pair(name)
    before, after = load_image(before_path), load_image(after_path)
    for method in ("diff", "ssim"):
        result = detect_changes(before, after, method=method)
        save_outputs(result, os.path.join("outputs", name, method))
        s = result["stats"]
        rows.append([name, method, f"{s['width']}x{s['height']}",
                     round(s["change_percent"], 3), s["regions"],
                     round(s["threshold"]), round(s["preprocess_ms"], 1),
                     round(s["change_map_ms"], 1), round(s["threshold_ms"], 1),
                     round(s["postprocess_ms"], 1), round(s["total_ms"], 1)])
        print(f"{name:<12}{method:<7}{s['change_percent']:>9.2f}"
              f"{s['regions']:>9}{s['threshold']:>6.0f}{s['total_ms']:>8.0f}")

with open("outputs/summary_day2.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["pair", "method", "size", "change_percent", "regions",
                     "otsu_threshold", "preprocess_ms", "change_map_ms",
                     "threshold_ms", "postprocess_ms", "total_ms"])
    writer.writerows(rows)
print("Saved outputs/summary_day2.csv")