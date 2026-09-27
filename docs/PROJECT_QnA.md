# AI-Based Remote Corrosion Inspection System  
## Project Overview & QnA Guide

Use this document to explain **what the system is**, **what technologies we chose and why**, **how the pieces connect**, and to prepare for **viva / QnA**.

---

## 1. One-line summary

An web-based prototype that accepts a corrosion image (plus optional temperature and humidity), runs AI object detection, estimates affected area and severity, suggests maintenance guidance, stores the inspection, and shows results on a dashboard.

> **Important:** This is a **college engineering prototype**. Severity and recommendations are **not** certified industrial standards. AI does **not** replace qualified physical inspection.

---

## 2. Problem we solved

Manual corrosion inspection is slow, inconsistent, and hard to track over time. This system provides:

1. **Remote visual inspection** — upload an image from a browser or camera device  
2. **AI-assisted detection** — find corrosion-related regions in the image  
3. **Structured assessment** — affected area %, severity, environmental context  
4. **Actionable output** — maintenance recommendation + inspection history  
5. **Hardware-ready API** — same endpoint for UI and future DHT11 / ESP32 devices  

---

## 3. High-level architecture

```
┌─────────────────┐         HTTP (JSON / multipart)        ┌──────────────────────────┐
│  Next.js UI     │ ─────────────────────────────────────► │  FastAPI Backend         │
│  (port 3000)    │ ◄───────────────────────────────────── │  (port 8000)             │
│                 │         results + image URLs            │                          │
│  Dashboard      │                                         │  Pipeline orchestrator   │
│  New Inspection │                                         │  ├── YOLO / Demo AI      │
│  History        │                                         │  ├── Area calculation    │
│  Detail page    │                                         │  ├── Severity engine     │
└─────────────────┘                                         │  ├── Env context         │
                                                            │  └── Recommendation      │
                                                            │           │              │
                                                            │           ▼              │
                                                            │  SQLite (default) or     │
                                                            │  MongoDB (optional)      │
                                                            │  + /uploads static files │
                                                            └──────────────────────────┘
```

**Connection rule:** The frontend never runs ML. It only talks to the backend over HTTP. The backend owns detection, scoring, storage, and image files.

---

## 4. Tech stack — what we used and why

| Layer | Technology | Why we used it |
|---|---|---|
| Frontend | **Next.js 16** (App Router) + **React 19** + **TypeScript** | Modern full-stack React framework; file-based routing for Dashboard / Inspect / History / Detail; TypeScript catches API shape mistakes early |
| Styling | **Tailwind CSS 4** | Fast UI styling without writing large CSS files |
| Charts | **Recharts** | Simple pie/bar charts for severity distribution and timeline on the dashboard |
| Backend | **Python 3.10+**, **FastAPI**, **Uvicorn** | FastAPI gives automatic OpenAPI docs (`/docs`), easy multipart uploads, and clear route structure — ideal for a demoable API |
| Config | **pydantic-settings** + `.env` | All thresholds and paths change without editing code |
| ML | **YOLOv8 (Ultralytics)** | Industry-standard object detection; runs locally on a `.pt` model; good for bounding-box corrosion/crack detection |
| Vision utils | **OpenCV**, **Pillow**, **NumPy** | Decode images, draw boxes, compute affected area from detections |
| Database | **SQLite** (default) / **MongoDB** (optional) | SQLite = zero setup for demos; MongoDB switchable via env for cloud / scale later |
| API contract | **multipart/form-data** | Same request format works for browser upload and hardware (image + temp + humidity + device_id) |

### Why not other common choices?

| Alternative | Why we didn’t (or deferred) |
|---|---|
| TensorFlow / custom CNN only | YOLO gives ready bounding boxes and class labels with less training boilerplate |
| Only MongoDB | Adds install friction for a campus demo; SQLite works offline immediately |
| Put ML in the browser | Models are heavy; server-side keeps one source of truth and works for hardware POSTs |
| Hard-coded thresholds | Viva/demo needs tunable, explainable rules via `.env` |

---

## 5. How everything is connected (end-to-end flow)

### Step-by-step inspection

1. User opens **New Inspection** (`/inspect`) on the frontend.  
2. User selects an image and optionally enters **temperature**, **humidity**, **device ID**.  
3. Frontend builds `FormData` and calls `POST http://localhost:8000/api/inspection` (`frontend/lib/api.ts`).  
4. Backend API route (`backend/app/api/inspection.py`):
   - validates sensor ranges  
   - sanitises `device_id`  
   - calls the **pipeline** (no DB logic inside the pipeline)  
5. Pipeline (`backend/app/services/pipeline.py`) does the core work:
   1. Validate image (type/size)  
   2. Save original to `uploads/`  
   3. Run **YOLO** or **Demo** detector  
   4. Calculate **affected area %** (union of bounding boxes ÷ image area)  
   5. Assess **environment** (notes + priority modifier)  
   6. Estimate **severity**  
   7. Generate **recommendation**  
   8. Draw annotated image and save it  
   9. Assemble a result dictionary (`inspection_id` like `INS_A1B2C3D4`)  
6. API saves the record via the **repository** (SQLite or MongoDB).  
7. JSON response returns to the UI; images are loaded from `/uploads/...`.  
8. Dashboard and History read `GET /api/statistics` and `GET /api/history`.

### Separation of concerns (good design answer for viva)

| Layer | Responsibility | Does **not** do |
|---|---|---|
| Frontend | UI, forms, charts, display | ML, severity math, DB writes |
| API routes | HTTP, validation, CORS, save | Heavy business logic |
| Pipeline | Orchestrate inspection steps | HTTP or database |
| Services | Detection, severity, env, recommendation | Know about FastAPI |
| Repository | Persist / query | Know about YOLO |

This makes the system easier to test and explain: each module has one job.

---

## 6. Backend modules (what each file does)

| Path | Role |
|---|---|
| `backend/app/main.py` | Creates FastAPI app, CORS, mounts `/uploads`, health check, loads detector on startup |
| `backend/app/config.py` | All settings from `.env` (thresholds, model path, DB, upload limits) |
| `backend/app/api/inspection.py` | HTTP endpoints for inspection, history, statistics |
| `backend/app/services/pipeline.py` | Full inspection orchestrator |
| `backend/app/services/inference.py` | `CorrosionDetector` interface → YOLO or Demo |
| `backend/app/services/severity.py` | Area-based severity + optional one-step promotion |
| `backend/app/services/environmental.py` | Temp/humidity notes and priority modifier |
| `backend/app/services/recommendation.py` | Maps severity → maintenance text |
| `backend/app/utils/image_utils.py` | Validate, annotate, affected-area calculation |
| `backend/app/database/repository.py` | Chooses SQLite vs MongoDB |
| `backend/app/database/sqlite_db.py` | Default storage |
| `backend/app/database/mongo_db.py` | Optional Mongo storage |
| `backend/app/schemas/inspection.py` | Pydantic response shapes |

---

## 7. Frontend modules

| Path | Role |
|---|---|
| `frontend/app/page.tsx` | Dashboard — stats, charts, recent inspections, health badge |
| `frontend/app/inspect/page.tsx` | Upload form + inline results |
| `frontend/app/history/page.tsx` | Filterable, paginated history |
| `frontend/app/inspection/[id]/page.tsx` | Full inspection detail |
| `frontend/lib/api.ts` | All backend API calls (single base URL) |
| `frontend/lib/utils.ts` | Formatting helpers |
| `frontend/types/inspection.ts` | Shared TypeScript types |
| `frontend/components/ui/*` | Severity badge, demo banner, disclaimer, stat cards |

Frontend ↔ Backend link: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

---

## 8. AI / inference

### Modes (`INFERENCE_MODE` in `.env`)

| Mode | Behaviour |
|---|---|
| `real` or `auto` | Load local YOLO model from `backend/models/corrosion.pt` |
| `demo` | Synthetic detections for tests / demos without a model |

Detection classes (from dataset): **corrosion**, **crack**, **slippage** (Roboflow corrosion-bi3q3 style).

### What YOLO returns

For each detection:

- `class` — label  
- `confidence` — 0–1 score  
- `bounding_box` — `[x1, y1, x2, y2]`  

### Affected area

Not pixel-perfect segmentation. We take the **union of bounding boxes** over the image and convert to a **percentage**. That estimate feeds severity.

---

## 9. Severity, environment, recommendation

### Severity (primarily by affected area %)

| Level | Default area rule |
|---|---|
| Low | ≤ 5% |
| Moderate | ≤ 20% |
| High | ≤ 50% |
| Critical | > 50% |

Thresholds are configurable: `LOW_MAX`, `MODERATE_MAX`, `HIGH_MAX` in `.env`.

**Promotion:** secondary factors can raise severity by **at most one level** when enough signals agree (e.g. many regions + elevated environment). High confidence alone mainly adds a note.

**No detection:** severity recorded as Low with reasoning “No corrosion detected…”, but recommendation uses the “none detected” text.

### Environment (DHT11-style context)

| Condition | Effect |
|---|---|
| Humidity ≥ 70% | Note + priority modifier |
| Temperature ≥ 35°C | Note + priority modifier |
| Both elevated | Stronger combined note |

**Critical viva point:** Temperature and humidity **do not predict corrosion by themselves**. They only add **contextual priority**. Detection still comes from the image/AI.

### Recommendation

Deterministic mapping:

| Input | Guidance idea |
|---|---|
| No detection | Continue routine monitoring |
| Low | Monitor; next maintenance interval |
| Moderate | Cleaning / coatings; schedule in cycle |
| High | Detailed inspection; prioritise |
| Critical | Immediate professional inspection |

Always accompanied by a disclaimer that a qualified human must decide.

---

## 10. Database

| | SQLite (default) | MongoDB |
|---|---|---|
| When | `MONGODB_URI` empty | URI set in `.env` |
| File / place | `backend/corrosion.db` | DB `corrosion_inspection` |
| Why | Instant demo, no server | Optional cloud / multi-machine later |

Stored fields include: `inspection_id`, timestamp, device_id, temp/humidity, detections, confidence, affected_area, severity, recommendation, image paths, and a full JSON snapshot.

---

## 11. API endpoints (quick reference)

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Status, inference mode, DB type, model available |
| `POST` | `/api/inspection` | Run full inspection (multipart) |
| `GET` | `/api/inspection/{id}` | One inspection |
| `GET` | `/api/history` | Paginated list + filters |
| `GET` | `/api/statistics` | Dashboard aggregates |
| `GET` | `/uploads/{file}` | Original / annotated images |
| — | `/docs` | Swagger UI |

Hardware can call the **same** `POST /api/inspection` with image + temperature + humidity + device_id.

---

## 12. How to run (for demos)

**Backend**

```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Frontend** (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

- UI: http://localhost:3000  
- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

---

## 13. Limitations (say these clearly in viva)

1. Prototype severity thresholds — **not** ASME / ISO / certified standards.  
2. Bounding-box area is an **estimate**, not exact physical corrosion area.  
3. Model detects visual patterns; it does **not** output engineering severity directly.  
4. Sensors provide **context**, not corrosion prediction.  
5. Recommendations are **guidance**, not work orders.  
6. No authentication (campus prototype scope).  
7. Demo mode detections are **synthetic** when enabled.  

---

## 14. Likely QnA (with short answers)

### Q1. What is the aim of this project?
**A:** To build a prototype remote corrosion inspection system that uses AI vision plus optional environmental readings to estimate severity, suggest maintenance actions, and keep inspection history — without claiming certified engineering judgment.

### Q2. Why FastAPI for the backend?
**A:** Fast development, automatic Swagger docs, excellent support for file uploads, clear async Python API — good for connecting a web UI and future hardware devices.

### Q3. Why Next.js for the frontend?
**A:** Structured pages (dashboard, inspect, history, detail), React components, TypeScript safety, and easy `fetch` to our REST API.

### Q4. Why YOLO and not just classify the whole image as corroded/not?
**A:** Object detection gives **where** corrosion is (boxes), which lets us estimate **affected area** and count regions — more useful for severity than a single yes/no label.

### Q5. How is severity calculated?
**A:** Mainly from affected area percentage using configurable thresholds (Low ≤5%, Moderate ≤20%, High ≤50%, else Critical). Secondary factors (many regions + elevated environment) can promote severity by one step. The model does not directly output severity.

### Q6. Do temperature and humidity detect corrosion?
**A:** No. They only provide **environmental context** and may increase inspection priority. Detection comes from the image model.

### Q7. How does the frontend talk to the backend?
**A:** Through REST calls in `frontend/lib/api.ts` to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Inspection uses multipart FormData; other endpoints use JSON GETs.

### Q8. How is data stored?
**A:** By default in SQLite (`corrosion.db`). If `MONGODB_URI` is set, the repository switches to MongoDB with the same interface — no pipeline changes.

### Q9. What happens if the database save fails?
**A:** The inspection result can still be returned to the user; a warning may be attached. Pipeline and storage are separated so scoring is not lost just because persistence fails.

### Q10. How would hardware (e.g. ESP32 + camera + DHT11) integrate?
**A:** The device POSTs to the same `/api/inspection` with image bytes, temperature, humidity, and device_id. No separate API is required.

### Q11. What is the pipeline and why isolate it?
**A:** `run_inspection()` runs validation → detect → area → env → severity → recommendation → annotate. It does not touch HTTP or DB, so it is testable and reusable.

### Q12. What is demo vs real mode?
**A:** Real/auto loads `models/corrosion.pt` via Ultralytics. Demo fabricates detections for testing/demo when explicitly enabled. The health endpoint and UI show which mode is active.

### Q13. What datasets / classes do you use?
**A:** Corrosion-related object classes such as corrosion, crack, and slippage (Roboflow-style YOLO dataset). The model file lives under `backend/models/`.

### Q14. Is this production-ready?
**A:** No. It is a prototype for demonstration and learning: no auth, prototype thresholds, estimated area, and required human verification.

### Q15. How did you test the backend?
**A:** pytest suite under `backend/tests/` covering API endpoints, severity boundaries, recommendations, environmental validation, image utils, and demo detector behaviour.

### Q16. Explain the request lifecycle in one sentence.
**A:** The UI (or device) uploads an image and sensors → FastAPI validates → pipeline detects and scores → repository stores → JSON + annotated image URLs return to the dashboard.

### Q17. Why SQLite first?
**A:** Zero configuration for demos and viva; file-based DB travels with the project; MongoDB remains optional when a shared server is needed.

### Q18. Where are uploaded images kept?
**A:** Under `backend/uploads/`, served statically at `/uploads/...` so the frontend can display originals and annotated results.

---

## 15. Demo script (2–3 minutes)

1. Open http://localhost:3000 — show dashboard + health (inference mode).  
2. Go to **New Inspection** — upload a sample corrosion image; enter e.g. temp `31.4`, humidity `72`, device `CAM_001`.  
3. Show result: boxes, area %, severity, environmental note, recommendation, disclaimer.  
4. Open full detail page.  
5. Show **History** and return to **Dashboard** charts updated.  
6. Optionally open http://localhost:8000/docs and point to the same POST endpoint for hardware.

---

## 16. Project folder map (mental model)

```
corrosion-detection/
├── backend/app/          ← API + ML + business logic
├── backend/models/       ← YOLO .pt weights
├── backend/uploads/      ← saved images
├── backend/tests/        ← pytest
├── frontend/app/         ← pages
├── frontend/lib/api.ts   ← backend client
├── docs/API.md           ← API reference
├── docs/PROJECT_QnA.md   ← this file
├── data/sample_images/   ← demo images
└── README.md             ← setup instructions
```

---

## 17. Key takeaway sentence (closing answer)

> We built a modular prototype where a Next.js UI and optional hardware share one FastAPI inspection API; YOLO finds corrosion regions, rule-based engines convert visual coverage and sensor context into transparent severity and maintenance guidance, and results are stored for dashboard and history — with clear disclaimers that this supports, not replaces, professional inspection.
