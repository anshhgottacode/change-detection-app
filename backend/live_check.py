import mimetypes
import os
import sys
import time

import requests

from pipeline import find_pair

API = os.getenv("API_URL", "").rstrip("/")
if not API:
    raise SystemExit("Set API_URL first, e.g. $env:API_URL='https://your-backend'")
pair = sys.argv[1] if len(sys.argv) > 1 else "pair1"
b, a = find_pair(pair)


def timed(label, fn):
    t = time.perf_counter()
    r = fn()
    ms = (time.perf_counter() - t) * 1000
    print(f"{label:<26} HTTP {r.status_code}  {ms:8.0f} ms")
    return r


def post(extra):
    files = {"before": (os.path.basename(b), open(b, "rb"), mimetypes.guess_type(b)[0] or "image/jpeg"),
             "after": (os.path.basename(a), open(a, "rb"), mimetypes.guess_type(a)[0] or "image/jpeg")}
    return requests.post(API + "/analyze", files=files, data=extra, timeout=300)


timed("GET /health (first)", lambda: requests.get(API + "/health", timeout=300))
timed("GET /health (second)", lambda: requests.get(API + "/health", timeout=300))
timed("GET /config", lambda: requests.get(API + "/config", timeout=60))

configs = [("diff", {"method": "diff"}),
           ("diff + align", {"method": "diff", "align": "true"}),
           ("ssim", {"method": "ssim"}),
           ("ssim + align", {"method": "ssim", "align": "true"})]
for label, extra in configs:
    r = timed(f"POST {label}", lambda e=extra: post({**e, "max_width": 960}))
    if r.ok:
        js = r.json()
        s, t = js["stats"], js["timing"]
        print(f"    change {s['change_percent']}%  regions {s['regions']}  "
              f"aligned {s['aligned']}  server request {t['request_ms']} ms  "
              f"payload {len(r.content) // 1024} KB")
    else:
        print("   ", r.text[:200])