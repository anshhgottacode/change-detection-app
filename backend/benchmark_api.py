import csv
import mimetypes
import os
import statistics as st
import sys
import time

import requests

from pipeline import find_pair

API = os.getenv("API_URL", "http://127.0.0.1:8000")
PAIR = sys.argv[1] if len(sys.argv) > 1 else "pair1"
WIDTHS = [640, 960, 1280]       # add 1920 only if your photo is at least that wide
CONFIGS = {
    "diff":       {"method": "diff"},
    "ssim":       {"method": "ssim"},
    "diff_align": {"method": "diff", "align": "true"},
    "ssim_align": {"method": "ssim", "align": "true"},
}
RUNS = 11                       # the first run is a warm-up and is discarded
KEYS = ["preprocess_ms", "align_ms", "change_map_ms", "threshold_ms",
        "postprocess_ms", "pipeline_ms", "decode_ms", "encode_ms", "request_ms"]

before_path, after_path = find_pair(PAIR)
bytes_before, bytes_after = open(before_path, "rb").read(), open(after_path, "rb").read()
mime = mimetypes.guess_type(before_path)[0] or "image/jpeg"

rows = []
for cfg, params in CONFIGS.items():
    for width in WIDTHS:
        samples = {k: [] for k in KEYS + ["client_ms", "payload_kb"]}
        actual_width = None
        for i in range(RUNS):
            files = {"before": ("b", bytes_before, mime), "after": ("a", bytes_after, mime)}
            data = {**params, "max_width": width}
            t = time.perf_counter()
            r = requests.post(f"{API}/analyze", files=files, data=data, timeout=180)
            client_ms = (time.perf_counter() - t) * 1000
            r.raise_for_status()
            js = r.json()
            if i == 0:
                actual_width = js["stats"]["width"]
                continue                       # discard warm-up
            for k in KEYS:
                samples[k].append(js["timing"][k])
            samples["client_ms"].append(client_ms)
            samples["payload_kb"].append(len(r.content) / 1024)
        row = {"pair": PAIR, "config": cfg, "max_width": width,
               "actual_width": actual_width, "runs": RUNS - 1}
        for k, v in samples.items():
            row[k + "_mean"] = round(st.mean(v), 1)
            row[k + "_std"] = round(st.stdev(v), 1)
        rows.append(row)
        print(f"{cfg:<11} w={width:<5} (actual {actual_width}) "
              f"pipeline {row['pipeline_ms_mean']:>7.1f} ±{row['pipeline_ms_std']:<5.1f} "
              f"request {row['request_ms_mean']:>7.1f}  client {row['client_ms_mean']:>7.1f} ms")

os.makedirs("outputs", exist_ok=True)
with open("outputs/benchmark_day4.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("Saved outputs/benchmark_day4.csv")