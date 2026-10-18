import glob
import os
import cv2

for p in sorted(glob.glob("../test_images/*")):
    img = cv2.imread(p)
    if img is None:
        continue
    h, w = img.shape[:2]
    print(f"{os.path.basename(p)}, {w}x{h}, {os.path.getsize(p) // 1024} KB")