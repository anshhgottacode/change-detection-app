import csv
import glob
import os

import numpy as np

from pipeline import load_image, find_pair, detect_changes


def pct(mask):
    return 100.0 * np.count_nonzero(mask) / mask.size


names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})

rows = []
print(f"{'pair':<12}{'blur':>5}{'raw %':>9}{'clean %':>9}{'final %':>9}{'regions':>9}")
for name in names:
    b, a = find_pair(name)
    before, after = load_image(b), load_image(a)
    for blur in (1, 5):
        r = detect_changes(before, after, method="diff", blur=blur)
        row = [name, blur, round(pct(r["mask_raw"]), 3),
               round(pct(r["mask_clean"]), 3),
               round(r["stats"]["change_percent"], 3), r["stats"]["regions"]]
        rows.append(row)
        print(f"{row[0]:<12}{row[1]:>5}{row[2]:>9.2f}{row[3]:>9.2f}"
              f"{row[4]:>9.2f}{row[5]:>9}")

print("\nMean ± std across pairs (population is only your test pairs):")
for blur in (1, 5):
    sel = np.array([r[2:] for r in rows if r[1] == blur], dtype=float)
    mean = sel.mean(axis=0)
    std = sel.std(axis=0, ddof=1) if len(sel) > 1 else np.zeros(4)
    print(f"blur {blur}: raw {mean[0]:.2f}±{std[0]:.2f}  clean {mean[1]:.2f}±{std[1]:.2f}  "
          f"final {mean[2]:.2f}±{std[2]:.2f}  regions {mean[3]:.1f}±{std[3]:.1f}")

os.makedirs("outputs", exist_ok=True)
with open("outputs/fig5_stats.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair", "blur", "raw_pct", "clean_pct", "final_pct", "regions"])
    w.writerows(rows)
print("Saved outputs/fig5_stats.csv")