import cv2
from pipeline import load_image, find_pair, detect_changes

print("OpenCV", cv2.__version__)
b, a = find_pair("shiftstatic")
before, after = load_image(b), load_image(a)
seen = set()
for i in range(10):
    s = detect_changes(before, after, method="diff", align=True)["stats"]
    row = (round(s["change_percent"], 3), s["regions"], s["inliers"],
           round(s["valid_percent"], 2))
    seen.add(row)
    print(i + 1, row)
print("distinct results:", len(seen))