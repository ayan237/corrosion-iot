# AI-Based Remote Corrosion Inspection System

> **College engineering prototype** — AI-powered visual corrosion inspection with environmental context, severity estimation, maintenance recommendations, and inspection history.
>
> ⚠ This is a prototype. Severity thresholds and recommendations are not certified engineering standards. AI inference does not replace qualified physical inspection.

---

## What it does

```
Upload Image  →  FastAPI Backend  →  AI Detection (YOLO / Demo)
                                  →  Affected Area Calculation
                                  →  Severity Engine
                                  →  Environmental Context (Temp + Humidity)
                                  →  AI Solution Prediction (Gemini Multimodal / Fallback)
                                  →  SQLite / MongoDB
                                  →  Next.js Dashboard
```

1. User uploads a corrosion image through the web UI (or hardware device sends it via API)
2. Backend validates the image and runs object detection
3. Detected bounding boxes are used to estimate the affected area
4. A severity level is assigned based on area, region count, and environmental conditions
5. A structured engineering maintenance solution is predicted via Google Gemini AI (with deterministic fallback)
6. The inspection is stored and displayed in the dashboard and history

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS, Recharts |
| Backend | Python 3.13, FastAPI 0.119, Uvicorn |
| ML / CV | YOLOv8 (Ultralytics) or Demo mode, OpenCV, Pillow, NumPy |
| AI Planning | Google Gemini 2.5/3.8 Flash (Multimodal Engineering Remediation) |
| Database | SQLite (default) · MongoDB (optional) |

---

## Quick start

### Prerequisites

- Python 3.10+ (tested on 3.13)
- Node.js 18+ (tested on 24)
- Git

### 1 — Clone and configure

```bash
git clone <repo-url>
cd corrosion-detection
```

Copy the environment template:

```bash
cp .env.example backend/.env
```

The defaults work out of the box (SQLite + demo mode). No changes required to run.

### 2 — Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate          # Windows PowerShell
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend is now running at **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**

### 3 — Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend is now running at **http://localhost:3000**

---

## Running tests

```powershell
cd backend
venv\Scripts\activate
pytest tests/ -v
```

Expected output: **98 tests passed**

Tests cover:
- All API endpoints (health, inspection, history, statistics)
- Severity engine — all boundary cases
- Recommendation engine — all severity levels
- Environmental validation and context
- Image validation and affected area calculation
- Demo detector — determinism and field validation

---

## Demo walkthrough

This is the primary acceptance test for demonstrations:

1. Open **http://localhost:3000**
2. Dashboard shows statistics (empty on first run)
3. Click **New Inspection**
4. Drop or select a corrosion image (JPG/PNG/WEBP)
5. Enter:
   - Temperature: `31.4`
   - Humidity: `72`
   - Device ID: `CAM_001`
6. Click **Run Inspection**
7. View the inline result:
   - Original image and annotated image with bounding boxes
   - Detected class + confidence
   - Affected area %
   - Severity level
   - Environmental context note
   - Maintenance recommendation
8. Click **View full detail page** to see the complete inspection
9. Go to **History** — the inspection appears in the table
10. Return to **Dashboard** — statistics and charts are updated

---

## Project structure

```
corrosion-detection/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory + lifespan
│   │   ├── config.py            # All configuration via pydantic-settings
│   │   ├── api/
│   │   │   └── inspection.py    # HTTP routes
│   │   ├── services/
│   │   │   ├── pipeline.py      # Inspection orchestrator
│   │   │   ├── inference.py     # CorrosionDetector interface + YOLO + Demo
│   │   │   ├── severity.py      # Severity engine
│   │   │   ├── recommendation.py # Deterministic recommendation engine
│   │   │   └── environmental.py # Environmental context + sensor validation
│   │   ├── database/
│   │   │   ├── repository.py    # DB router (SQLite / MongoDB)
│   │   │   ├── sqlite_db.py     # SQLite implementation
│   │   │   └── mongo_db.py      # MongoDB implementation
│   │   ├── utils/
│   │   │   └── image_utils.py   # Validation, preprocessing, annotation, area
│   │   └── schemas/
│   │       └── inspection.py    # Pydantic response schemas
│   ├── models/                  # Place YOLO .pt model files here
│   ├── uploads/                 # Uploaded and annotated images
│   ├── tests/                   # pytest test suite (98 tests)
│   ├── requirements.txt
│   └── .env                     # Local config (not committed)
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Dashboard
│   │   ├── inspect/page.tsx     # New inspection
│   │   ├── history/page.tsx     # Inspection history
│   │   └── inspection/[id]/page.tsx  # Detail view
│   ├── components/
│   │   ├── Navbar.tsx
│   │   └── ui/                  # SeverityBadge, DemoBanner, Disclaimer, StatCard
│   ├── lib/
│   │   ├── api.ts               # All backend API calls
│   │   └── utils.ts             # Formatting and colour helpers
│   ├── types/
│   │   └── inspection.ts        # Shared TypeScript types
│   └── .env.local               # NEXT_PUBLIC_API_URL
│
├── data/
│   └── sample_images/           # Add test images here for demos
│
├── docs/
│   └── API.md                   # Full API reference
│
├── .env.example                 # Environment variable documentation
├── .gitignore
└── README.md
```

---

## Configuration reference

All configuration is done through `backend/.env`. Copy from `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URI` | _(empty)_ | MongoDB connection string. Leave empty to use SQLite. |
| `DATABASE_NAME` | `corrosion_inspection` | Database name |
| `SQLITE_PATH` | `corrosion.db` | SQLite file path (relative to backend/) |
| `MODEL_PATH` | `models/corrosion.pt` | Path to YOLO .pt model file |
| `INFERENCE_MODE` | `auto` | `auto` / `demo` / `real` |
| `UPLOAD_DIR` | `uploads` | Directory for saved images |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum image upload size |
| `LOW_MAX` | `5` | Affected area % upper bound for Low severity |
| `MODERATE_MAX` | `20` | Upper bound for Moderate severity |
| `HIGH_MAX` | `50` | Upper bound for High severity (above = Critical) |
| `HUMIDITY_ELEVATED_THRESHOLD` | `70` | Humidity % that triggers elevated note |
| `TEMP_HIGH_THRESHOLD` | `35` | Temperature °C that triggers high-temp note |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → backend URL |

---

## Adding a real ML model

The system runs in **Demo mode** by default — detections are synthetic.
To use real AI inference:

### Option A — Download the Roboflow corrosion-bi3q3 model

1. Create a free account at [Roboflow](https://roboflow.com)
2. Go to [corrosion-bi3q3](https://universe.roboflow.com/roboflow-100/corrosion-bi3q3)
3. Export the model as **YOLOv8 PyTorch** (`.pt` format)
4. Place the file at `backend/models/corrosion.pt`
5. Install Ultralytics: `pip install ultralytics`
6. In `backend/.env`, set `INFERENCE_MODE=auto` (or leave as default)
7. Restart the backend — it will load the real model automatically

### Option B — Train a custom model

1. Collect and annotate corrosion images using [Roboflow](https://roboflow.com) or Label Studio
2. Train with YOLOv8: `yolo train data=dataset.yaml model=yolov8n.pt`
3. Place the resulting `best.pt` at `backend/models/corrosion.pt`
4. Update `MODEL_PATH` in `.env` if using a different path

### Verify real inference is active

Check `/api/health`:
```json
{ "inference_mode": "real", "model_available": true }
```

The dashboard and inspection pages also show the current mode.

---

## MongoDB setup (optional)

SQLite works out of the box. To use MongoDB:

1. Install and start MongoDB locally, or use [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier)
2. Set `MONGODB_URI` in `backend/.env`:
   ```
   MONGODB_URI=mongodb://localhost:27017
   ```
3. Restart the backend

---

## Hardware integration

The same `POST /api/inspection` endpoint accepts submissions from any device.

**Hardware team sends:**
```
POST http://<server-ip>:8000/api/inspection
Content-Type: multipart/form-data

image       = <captured image bytes>
temperature = <DHT11 reading>
humidity    = <DHT11 reading>
device_id   = <device identifier>
```

No separate endpoint or software changes are needed. See `docs/API.md` for the full contract.

---

## Accuracy disclaimers

Per PRD section 30 — these rules are enforced throughout the system:

1. The detection model does **not** directly predict engineering severity
2. DHT11 readings do **not** predict corrosion — they are contextual only
3. Severity thresholds are prototype estimates, **not** industry standards
4. AI does **not** replace qualified physical inspection
5. Bounding box area is an **estimate**, not exact physical corrosion area
6. Demo mode detections are **synthetic** and clearly labelled as such
7. No model accuracy claims are made for the prototype

---

## API documentation

Full endpoint reference: [`docs/API.md`](docs/API.md)

Interactive Swagger UI (when backend is running): http://localhost:8000/docs

---

## Expected URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/api/health |
#   c o r r o s i o n - p r o j e c t  
 