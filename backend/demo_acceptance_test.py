"""
PRD section 28 — Demo acceptance test.
Runs the full demo flow described in the PRD programmatically.
"""
import io, json, httpx
from PIL import Image, ImageDraw

API = "http://127.0.0.1:8000"
UI  = "http://localhost:3000"
client = httpx.Client(timeout=30)

print("=" * 60)
print("CORROSION INSPECTION — DEMO ACCEPTANCE TEST")
print("=" * 60)

# ── Step 1: Dashboard reachable ──────────────────────────────────────────
r = client.get(f"{UI}/")
assert r.status_code == 200
print("[PASS] 1. Dashboard loads (HTTP 200)")

# ── Step 2: Backend health ────────────────────────────────────────────────
r = client.get(f"{API}/api/health")
h = r.json()
assert h["status"] == "ok"
print(f"[PASS] 2. Backend health OK — mode={h['inference_mode']}, db={h['database']}")

# ── Step 3: Create a realistic test image (corrosion-like texture) ────────
img = Image.new("RGB", (640, 480), color=(90, 60, 40))
draw = ImageDraw.Draw(img)
# Add some orange/rust patches to simulate corrosion
draw.ellipse([100, 80, 280, 220],  fill=(160, 80, 30))
draw.ellipse([350, 200, 500, 360], fill=(140, 90, 20))
draw.rectangle([50, 300, 200, 400], fill=(120, 70, 25))
buf = io.BytesIO(); img.save(buf, format="JPEG"); img_bytes = buf.getvalue()
print(f"[PASS] 3. Test image prepared ({len(img_bytes):,} bytes, 640×480)")

# ── Step 4: Run inspection (PRD demo values) ──────────────────────────────
r = client.post(
    f"{API}/api/inspection",
    files={"image": ("corrosion_demo.jpg", img_bytes, "image/jpeg")},
    data={"temperature": "31.4", "humidity": "72", "device_id": "CAM_001"},
)
assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
ins = r.json()
print(f"[PASS] 4. Inspection created: {ins['inspection_id']}")

# ── Step 5: Verify all pipeline outputs ──────────────────────────────────
assert ins["inspection_id"].startswith("INS_"),          "Bad ID format"
assert isinstance(ins["detected"], bool),                "Missing detected"
assert isinstance(ins["detections"], list),              "Missing detections"
assert isinstance(ins["affected_area"], (int, float)),   "Missing affected_area"
assert ins["severity"] in ("Low","Moderate","High","Critical"), "Bad severity"
assert ins["temperature"] == 31.4,                       "Temperature not stored"
assert ins["humidity"] == 72.0,                          "Humidity not stored"
assert ins["device_id"] == "CAM_001",                    "Device ID not stored"
assert len(ins["recommendation"]) > 20,                  "Missing recommendation"
assert ins["environmental_note"],                        "Missing env note"
assert ins["inference_mode"] in ("real","demo"),         "Bad inference_mode"
assert ins["annotated_image_url"],                       "Missing annotated image"
print(f"[PASS] 5. Pipeline outputs verified:")
print(f"         detected={ins['detected']}, "
      f"area={ins['affected_area']:.1f}%, "
      f"severity={ins['severity']}, "
      f"mode={ins['inference_mode']}")

# ── Step 6: Bounding boxes visible ───────────────────────────────────────
if ins["detected"]:
    for d in ins["detections"]:
        bb = d["bounding_box"]
        assert len(bb) == 4, "Bad bounding box"
        assert bb[2] > bb[0] and bb[3] > bb[1], "Invalid box dimensions"
    print(f"[PASS] 6. {len(ins['detections'])} bounding box(es) validated")
else:
    print("[PASS] 6. No detections (valid result for this image hash)")

# ── Step 7: Annotated image accessible ───────────────────────────────────
ann_url = f"{API}{ins['annotated_image_url']}"
r = client.get(ann_url)
assert r.status_code == 200, f"Annotated image not served: {ann_url}"
assert r.headers["content-type"].startswith("image/"), "Not an image response"
print(f"[PASS] 7. Annotated image served ({len(r.content):,} bytes)")

# ── Step 8: Fetch stored inspection by ID ────────────────────────────────
iid = ins["inspection_id"]
r = client.get(f"{API}/api/inspection/{iid}")
assert r.status_code == 200
fetched = r.json()
assert fetched["inspection_id"] == iid
assert fetched["severity"] == ins["severity"]
print(f"[PASS] 8. Inspection retrieved from database: {iid}")

# ── Step 9: History page reachable ────────────────────────────────────────
r = client.get(f"{UI}/history")
assert r.status_code == 200
print("[PASS] 9. History page loads (HTTP 200)")

# ── Step 10: History API contains the new inspection ─────────────────────
r = client.get(f"{API}/api/history")
hist = r.json()
ids = [item["inspection_id"] for item in hist["items"]]
assert iid in ids, f"{iid} not found in history"
print(f"[PASS] 10. Inspection appears in history ({hist['total']} total records)")

# ── Step 11: Detail page reachable ───────────────────────────────────────
r = client.get(f"{UI}/inspection/{iid}")
assert r.status_code == 200
print(f"[PASS] 11. Inspection detail page loads: /inspection/{iid}")

# ── Step 12: Dashboard statistics updated ────────────────────────────────
r = client.get(f"{API}/api/statistics")
stats = r.json()
assert stats["total_inspections"] >= 1
assert 0.0 <= stats["detection_rate"] <= 100.0
assert isinstance(stats["severity_distribution"], dict)
print(f"[PASS] 12. Dashboard statistics updated:")
print(f"         total={stats['total_inspections']}, "
      f"detected={stats['corrosion_detected']}, "
      f"rate={stats['detection_rate']}%")

# ── Step 13: Error handling ───────────────────────────────────────────────
r_bad = client.post(f"{API}/api/inspection",
                    files={"image": ("x.jpg", b"not-an-image", "image/jpeg")})
assert r_bad.status_code == 422, f"Expected 422, got {r_bad.status_code}"
print("[PASS] 13. Invalid image correctly rejected (422)")

r_404 = client.get(f"{API}/api/inspection/DOES_NOT_EXIST")
assert r_404.status_code == 404
print("[PASS] 14. Non-existent inspection returns 404")

print()
print("=" * 60)
print("ALL DEMO ACCEPTANCE TESTS PASSED ✓")
print("=" * 60)
print()
print(f"  Frontend  : {UI}")
print(f"  Backend   : {API}")
print(f"  Swagger   : {API}/docs")
print(f"  Last run  : inspection {iid}")
print(f"  Mode      : {ins['inference_mode'].upper()}")
