import glob
import os

from pipeline import load_image, find_pair, detect_changes

names = sorted({os.path.basename(p).split("_before")[0]
                for p in glob.glob("../test_images/*_before.*")})
print(f"{'pair':<12}{'V1 thr':>8}{'V3 thr':>8}{'V3 overlap %':>14}")
for n in names:
    b, a = find_pair(n)
    before, after = load_image(b), load_image(a)
    s1 = detect_changes(before, after, method="diff")["stats"]
    s3 = detect_changes(before, after, method="diff", align=True)["stats"]
    print(f"{n:<12}{s1['threshold']:>8.0f}{s3['threshold']:>8.0f}{s3['valid_percent']:>14.1f}")