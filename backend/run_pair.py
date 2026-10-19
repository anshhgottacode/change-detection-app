import argparse
import os

from pipeline import load_image, find_pair, detect_changes, save_outputs

parser = argparse.ArgumentParser()
parser.add_argument("pair", help="pair name, e.g. shiftstatic")
parser.add_argument("--method", choices=["diff", "ssim"], default="diff")
parser.add_argument("--blur", type=int, default=5)
parser.add_argument("--threshold", type=int, default=None)
parser.add_argument("--kernel", type=int, default=5)
parser.add_argument("--min-area", type=int, default=200)
parser.add_argument("--align", action="store_true")
parser.add_argument("--normalize", choices=["none", "clahe", "match"], default="none")
parser.add_argument("--features", type=int, default=3000)
parser.add_argument("--ratio", type=float, default=0.75)
parser.add_argument("--tag", default="", help="suffix for the output folder")
args = parser.parse_args()

before_path, after_path = find_pair(args.pair)
result = detect_changes(
    load_image(before_path), load_image(after_path),
    method=args.method, blur=args.blur, threshold=args.threshold,
    morph_kernel=args.kernel, min_area=args.min_area,
    align=args.align, normalize=None if args.normalize == "none" else args.normalize,
    orb_features=args.features, ratio=args.ratio,
)

name = args.method + ("_align" if args.align else "")
if args.normalize != "none":
    name += "_" + args.normalize
folder = os.path.join("outputs", args.pair, name + args.tag)
save_outputs(result, folder)

s = result["stats"]
print(f"Saved to {folder}")
print(f"Change: {s['change_percent']:.2f}%  Regions: {s['regions']}  "
      f"Threshold: {s['threshold']:.0f}  Time: {s['total_ms']:.0f} ms")
if args.align:
    print(f"Aligned: {s['aligned']}  keypoints: {s['keypoints_before']}/"
          f"{s['keypoints_after']}  good matches: {s['matches']}  "
          f"inliers: {s['inliers']}  {s['align_reason']}")