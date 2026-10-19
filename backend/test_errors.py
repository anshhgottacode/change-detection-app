import os

import cv2
import numpy as np
import requests

API = os.getenv("API_URL", "http://127.0.0.1:8000")


def png(w, h):
    img = np.random.randint(0, 255, (h, w, 3), np.uint8)
    return cv2.imencode(".png", img)[1].tobytes()


def f(name, data, mime="image/png"):
    return (name, data, mime)


good = png(200, 200)
tests = [
    ("valid pair", {"before": f("a.png", good), "after": f("b.png", good)}, {}, 200),
    ("text file as image", {"before": f("a.txt", b"hello", "text/plain"),
                            "after": f("b.png", good)}, {}, 400),
    ("empty file", {"before": f("a.png", b""), "after": f("b.png", good)}, {}, 400),
    ("image too small", {"before": f("a.png", png(10, 10)), "after": f("b.png", good)}, {}, 400),
    ("file too large", {"before": f("big.jpg", os.urandom(11 * 1024 * 1024), "image/jpeg"),
                        "after": f("b.png", good)}, {}, 413),
    ("blur out of range", {"before": f("a.png", good), "after": f("b.png", good)}, {"blur": "99"}, 422),
    ("unknown method", {"before": f("a.png", good), "after": f("b.png", good)}, {"method": "magic"}, 422),
    ("threshold out of range", {"before": f("a.png", good), "after": f("b.png", good)}, {"threshold": "300"}, 422),
    ("missing after image", {"before": f("a.png", good)}, {}, 422),
]

passed = 0
for name, files, data, expected in tests:
    r = requests.post(f"{API}/analyze", files=files, data=data, timeout=60)
    ok = r.status_code == expected
    passed += ok
    detail = "" if r.status_code == 200 else str(r.json().get("detail"))[:80]
    print(f"[{'PASS' if ok else 'FAIL'}] {name:<26} expected {expected}, got {r.status_code}  {detail}")
print(f"\n{passed}/{len(tests)} passed")