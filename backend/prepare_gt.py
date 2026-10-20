
import os
import sys
import cv2
import numpy as np

from pipeline import load_image, find_pair, detect_changes

names = sys.argv[1:] or ["pair1", "pair2", "pair3"]

template_dir = "../ground_truth/templates"
mask_dir = "../ground_truth/masks"

os.makedirs(template_dir, exist_ok=True)
os.makedirs(mask_dir, exist_ok=True)

for name in names:
    before_path, after_path = find_pair(name)
    before_img = load_image(before_path)
    after_img = load_image(after_path)

    result = detect_changes(
        before_img,
        after_img,
        method="diff",
        align=True
    )

    before = result["before"]
    after = (
        result["after_aligned"]
        if result["after_aligned"] is not None
        else result["after"]
    )

    h, w = before.shape[:2]

    cv2.imwrite(f"{template_dir}/{name}_before.png", before)
    cv2.imwrite(f"{template_dir}/{name}_after.png", after)

    # Valid overlap: exclude warped borders when alignment succeeds.
    valid = result["valid"]
    if valid is None:
        valid = np.full((h, w), 255, dtype=np.uint8)

    cv2.imwrite(f"{mask_dir}/{name}_valid.png", valid)

    # Blank mask for MANUAL ground-truth annotation.
    # White = changed; black = unchanged.
    # Annotate only valid overlapping regions.
    gt_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.imwrite(f"{mask_dir}/{name}_mask.png", gt_mask)

    print(
        f"{name}: {w}x{h} | "
        f"aligned={result['stats']['aligned']} | "
        f"overlap={result['stats']['valid_percent']:.1f}% | "
        f"mask={w}x{h}",
        flush=True
    )
