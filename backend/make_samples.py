import os

import cv2

from pipeline import find_pair, load_image

SAMPLES = {"objects": "pair1", "shift": "shiftstatic", "light": "lightstatic"}
out = "../frontend/public/samples"
os.makedirs(out, exist_ok=True)
for name, pair in SAMPLES.items():
    b, a = find_pair(pair)
    for role, path in (("before", b), ("after", a)):
        img = load_image(path)
        h, w = img.shape[:2]
        if w > 1000:
            img = cv2.resize(img, (1000, int(h * 1000 / w)), interpolation=cv2.INTER_AREA)
        dst = os.path.join(out, f"{name}_{role}.jpg")
        cv2.imwrite(dst, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(dst, os.path.getsize(dst) // 1024, "KB")