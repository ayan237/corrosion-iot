# Final Project Startup & Test Guide

How to start the full **AI-Based Remote Corrosion Inspection** system and verify it works end-to-end.

> Prototype only — severity and recommendations are not certified engineering standards.

---

## What you need

| Tool | Version |
|---|---|
| Python | 3.10+ (tested on 3.13) |
| Node.js | 18+ (tested on 24) |
| npm | comes with Node |
| Git | any recent version |

Optional (not required for demo mode):

- Google Gemini API key — AI maintenance solutions
- YOLO `.pt` model at `backend/models/corrosion.pt` — real detection
- Arduino + OV7670 — hardware capture (see `hardware/README.md`)

---

## One-time setup

### 1. Clone / open the project

```powershell
cd C:\corrosion-detection
```

### 2. Backend environment

```powershell
# Copy env template (defaults = SQLite + demo mode — works immediately)
copy .env.example backend\.env

cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend environment

```powershell
cd C:\corrosion-detection\frontend
npm install
```

Create `frontend\.env.local` if it does not exist:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Start the whole project

You need **two terminals**. Keep both running.

### Terminal 1 — Backend (port 8000)

```powershell
cd C:\corrosion-detection\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

| Check | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

Expected health response includes `"status": "ok"`.

### Terminal 2 — Frontend (port 3000)

```powershell
cd C:\corrosion-detection\frontend
npm run dev
```

| Check | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| New Inspection | http://localhost:3000/inspect |
| History | http://localhost:3000/history |

---

## How to test

### A. Automated unit / API tests (backend only)

Backend does **not** need to be running for pytest (tests use FastAPI TestClient).

```powershell
cd C:\corrosion-detection\backend
.\venv\Scripts\activate
pytest tests/ -v
```

Covers:

- Health, inspection, history, statistics APIs
- Severity and recommendation engines
- Environmental validation
- Image validation and affected-area logic
- Demo detector behaviour
- Gemini service fallbacks

All tests should pass.

### B. Demo acceptance test (full stack)

Requires **both** backend and frontend running.

```powershell
cd C:\corrosion-detection\backend
.\venv\Scripts\activate
python demo_acceptance_test.py
```

This checks:

1. Dashboard loads  
2. Backend health  
3. Creates an inspection via API  
4. Pipeline fields (severity, area, recommendation, env note)  
5. Annotated image is served  
6. History + detail pages  
7. Statistics update  
8. Error handling (422 / 404)

Success ends with: `ALL DEMO ACCEPTANCE TESTS PASSED`

### C. Manual UI walkthrough (primary demo)

1. Open http://localhost:3000  
2. Open **New Inspection**  
3. Upload an image (`test.jpg` in the repo root, or any JPG/PNG/WEBP)  
4. Enter temperature `31.4`, humidity `72`, device ID `CAM_001`  
5. Click **Run Inspection**  
6. Confirm you see:
   - Original + annotated images  
   - Detections / confidence  
   - Affected area %  
   - Severity  
   - Environmental note  
   - Maintenance recommendation  
7. Open **History** — the new record appears  
8. Return to **Dashboard** — stats/charts update  

### D. Quick API smoke test (Swagger)

1. Open http://localhost:8000/docs  
2. Call `GET /api/health`  
3. Call `POST /api/inspection` with an image + temp/humidity/device_id  
4. Call `GET /api/history` and `GET /api/statistics`  

---

## Optional: hardware (camera → AI)

With the backend running:

```powershell
cd C:\corrosion-detection\hardware
..\backend\venv\Scripts\python.exe capture_final.py --inspect
```

This captures from the OV7670 (COM port auto-detected), enhances the frame, and posts to `POST /api/inspection`.

Full wiring and focus steps: [`hardware/README.md`](hardware/README.md).

---

## Optional config

Edit `backend/.env`:

| Goal | Setting |
|---|---|
| Force demo detections | `INFERENCE_MODE=demo` |
| Use real YOLO model | Place `backend/models/corrosion.pt`, set `INFERENCE_MODE=auto` |
| Gemini AI solutions | Set `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/app/apikey)) |
| MongoDB instead of SQLite | Set `MONGODB_URI=mongodb://localhost:27017` |

Leave blanks / defaults for a working demo with no extra accounts.

---

## Startup checklist

- [ ] `backend/.env` exists (copied from `.env.example`)
- [ ] Backend venv created and `pip install -r requirements.txt` done
- [ ] Frontend `npm install` done
- [ ] `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Backend on :8000 — health returns `ok`
- [ ] Frontend on :3000 — dashboard loads
- [ ] `pytest tests/ -v` passes
- [ ] `python demo_acceptance_test.py` passes (both servers up)
- [ ] Manual inspection upload works in the UI

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Frontend cannot reach API | Confirm backend is up; check `NEXT_PUBLIC_API_URL` |
| Port 8000 / 3000 in use | Stop the other process, or change the port and update `.env` / `.env.local` |
| `ModuleNotFoundError` | Activate `backend\venv` and re-run `pip install -r requirements.txt` |
| Empty / odd detections | Normal in **demo** mode (synthetic). For real AI, add `models/corrosion.pt` |
| Gemini not used | `GEMINI_API_KEY` empty → deterministic recommendation fallback (still valid) |
| Hardware COM not found | Plug in Arduino (CH340), then re-run `capture_final.py` |

---

## Useful URLs (when running)

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

More detail: [`README.md`](README.md) · API: [`docs/API.md`](docs/API.md) · Hardware: [`hardware/README.md`](hardware/README.md)
