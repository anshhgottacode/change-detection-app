import argparse
import os

from pipeline import load_image, find_pair, detect_changes, save_outputs

parser = argparse.ArgumentParser()
parser.add_argument("pair", help="pair name, e.g. pair1")
parser.add_argument("--method", choices=["diff", "ssim"], default="ssim")
parser.add_argument("--blur", type=int, default=5)
parser.add_argument("--threshold", type=int, default=None)
parser.add_argument("--kernel", type=int, default=5)
parser.add_argument("--min-area", type=int, default=200)
parser.add_argument("--tag", default="", help="suffix for the output folder")
args = parser.parse_args()

before_path, after_path = find_pair(args.pair)
result = detect_changes(
    load_image(before_path), load_image(after_path),
    method=args.method, blur=args.blur, threshold=args.threshold,
    morph_kernel=args.kernel, min_area=args.min_area,
)

folder = os.path.join("outputs", args.pair, args.method + args.tag)
save_outputs(result, folder)

s = result["stats"]
print(f"Saved to {folder}")
print(f"Change: {s['change_percent']:.2f}%  Regions: {s['regions']}  "
      f"Threshold: {s['threshold']:.0f}  Time: {s['total_ms']:.0f} ms")