import argparse
import base64
import mimetypes
import os

import requests

from pipeline import find_pair

parser = argparse.ArgumentParser()
parser.add_argument("pair")
parser.add_argument("--method", default="diff")
parser.add_argument("--align", action="store_true")
parser.add_argument("--normalize", default="none")
parser.add_argument("--blur", type=int, default=5)
parser.add_argument("--threshold", default="")
parser.add_argument("--api", default=os.getenv("API_URL", "http://127.0.0.1:8000"))
args = parser.parse_args()

before_path, after_path = find_pair(args.pair)


def part(path):
    return (os.path.basename(path), open(path, "rb"),
            mimetypes.guess_type(path)[0] or "image/jpeg")


data = {"method": args.method, "blur": args.blur, "threshold": args.threshold,
        "align": str(args.align).lower(), "normalize": args.normalize}
r = requests.post(f"{args.api}/analyze",
                  files={"before": part(before_path), "after": part(after_path)},
                  data=data, timeout=120)
print("HTTP", r.status_code, f"({len(r.content) / 1024:.0f} KB)")
if r.status_code != 200:
    print(r.text)
    raise SystemExit(1)

out = r.json()
print("stats :", out["stats"])
print("timing:", out["timing"])

folder = os.path.join("outputs", "api_test",
                      f"{args.pair}_{args.method}{'_align' if args.align else ''}")
os.makedirs(folder, exist_ok=True)
for name, uri in out["images"].items():
    header, b64 = uri.split(",", 1)
    ext = "png" if "png" in header else "jpg"
    with open(os.path.join(folder, f"{name}.{ext}"), "wb") as f:
        f.write(base64.b64decode(b64))
print("Saved images to", folder)