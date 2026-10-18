import os
import cv2
import numpy as np

# ---------- 1. Load images ----------
before = cv2.imread("../test_images/pair1_before.jpeg")
after = cv2.imread("../test_images/pair1_after.jpeg")

if before is None or after is None:
    raise SystemExit("Could not load images. Check names in the test_images folder.")

# Make the second image the same size as the first
after = cv2.resize(after, (before.shape[1], before.shape[0]))

# ---------- 2. Preprocess: grayscale + blur ----------
gray_before = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
gray_after = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

gray_before = cv2.GaussianBlur(gray_before, (5, 5), 0)
gray_after = cv2.GaussianBlur(gray_after, (5, 5), 0)

# ---------- 3. Difference ----------
diff = cv2.absdiff(gray_before, gray_after)

# ---------- 4. Threshold (Otsu picks the cutoff automatically) ----------
_, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# ---------- 5. Clean the mask ----------
kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # remove tiny specks
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # fill small holes

# ---------- 6. Find changed regions and draw boxes ----------
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = after.copy()
region_count = 0

for c in contours:
    if cv2.contourArea(c) >= 200:  # ignore very small regions
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)
        region_count += 1

# ---------- 7. Stats and heatmap ----------
change_percent = 100 * np.count_nonzero(mask) / mask.size
heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)

print(f"Changed regions: {region_count}")
print(f"Change percentage: {change_percent:.2f}%")

# ---------- 8. Save every stage ----------
os.makedirs("outputs", exist_ok=True)
cv2.imwrite("outputs/1_diff.png", diff)
cv2.imwrite("outputs/2_mask.png", mask)
cv2.imwrite("outputs/3_heatmap.png", heatmap)
cv2.imwrite("outputs/4_result_boxes.png", result)
print("Saved results in the outputs folder.")