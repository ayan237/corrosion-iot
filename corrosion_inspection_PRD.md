# PRD: AI-Based Remote Corrosion Inspection & Maintenance System

## 1. Project Overview

Build a working college-level engineering prototype for **AI-powered remote visual corrosion inspection**.

The system is designed around a future hardware device that captures corrosion images from areas that may be difficult, dangerous, or inconvenient for humans to physically inspect. The software must work independently of the hardware during development.

The complete software flow is:

```text
Image Upload / Hardware Image
        ↓
FastAPI Backend
        ↓
Image Preprocessing
        ↓
Corrosion Object Detection
        ↓
Affected Area Calculation
        ↓
Severity Estimation
        ↓
Environmental Context
        ↓
Maintenance Recommendation
        ↓
Database
        ↓
Web Dashboard
```

The hardware team will eventually provide:

- Image
- Temperature
- Humidity
- Device ID / inspection ID

The software must not depend on the physical hardware being available.

---

# 2. Primary Objective

Build a working end-to-end application where:

> A user uploads a corrosion image → AI detects corrosion → affected area is calculated → severity is estimated → temperature/humidity are incorporated as environmental context → a maintenance recommendation is generated → the inspection is stored → the dashboard displays the result and history.

This is a prototype. Do not present prototype severity thresholds or recommendations as certified engineering standards.

---

# 3. Target Users

### Primary

- Engineering students demonstrating the system
- Maintenance/inspection personnel in a prototype scenario
- Faculty/judges evaluating the project

### Secondary

- Future hardware operator
- Technician reviewing inspection history

---

# 4. Required Tech Stack

Use simple, free/open-source technologies.

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Recharts or another free charting library if charts are required

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

## ML / Computer Vision

- Python
- OpenCV
- Pillow
- NumPy
- YOLO/object detection
- Roboflow corrosion model as the initial model

Initial model reference:

https://universe.roboflow.com/roboflow-100/corrosion-bi3q3

Do not invent model capabilities or labels.

The known starting model includes classes such as:

- Corrosion
- Crack
- Slippage

The detection model should be treated as an object detector. It should NOT be claimed to directly predict engineering severity.

## Database

Prefer:

- MongoDB

If MongoDB configuration would unnecessarily block local development, provide a clean SQLite fallback.

## Development

- Git/GitHub
- VS Code/Cursor/Kiro or similar AI coding IDE
- Postman for API testing

---

# 5. Architecture

Use this architecture:

```text
                    ┌──────────────────────┐
                    │      Next.js UI      │
                    │ React + TypeScript   │
                    └──────────┬───────────┘
                               │
                               │ REST API
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │      Backend         │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       Image Processing       ML Model     Sensor Context
              │                │          Temp + Humidity
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Severity Engine      │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Recommendation Engine│
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │      Database        │
                    └──────────────────────┘
```

Keep the architecture modular.

The backend must not care whether an image came from:

- Frontend upload
- Arduino + OV7670
- ESP32
- Raspberry Pi
- USB camera
- Another embedded device

All sources should eventually use the same backend interface.

---

# 6. Repository Structure

Create a clean monorepo:

```text
corrosion-inspection/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── inference.py
│   │   │   ├── severity.py
│   │   │   ├── recommendation.py
│   │   │   └── environmental.py
│   │   ├── database/
│   │   └── utils/
│   ├── models/
│   ├── uploads/
│   ├── requirements.txt
│   └── ...
│
├── data/
│   ├── sample_images/
│   └── README.md
│
├── docs/
│   └── API.md
│
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

The exact structure can be adjusted if the agent has a better reason, but keep frontend/backend separation clear.

---

# 7. Core Features

## 7.1 Dashboard

Create a professional but simple engineering dashboard.

Display:

- Total inspections
- Corrosion detections
- High-severity inspections
- Critical inspections
- Recent inspections
- Latest environmental readings
- Detection rate
- Severity distribution

Do not overload the dashboard with unnecessary widgets.

---

# 8. Inspection Page

Create an inspection interface.

User should be able to:

1. Upload an image
2. Enter temperature
3. Enter humidity
4. Optionally enter device ID
5. Click `Run Inspection`

Example:

```text
Image: corrosion.jpg

Temperature: 31.4 °C
Humidity: 72 %
Device ID: CAM_001

[ Run Inspection ]
```

For development, temperature and humidity can be manually entered.

Later the hardware can send the same fields automatically.

---

# 9. Detection Pipeline

When the user submits an image:

### Step 1

Validate image format.

Support at minimum:

- JPG/JPEG
- PNG
- WEBP

Reject invalid files gracefully.

### Step 2

Preprocess the image if required by the selected model.

### Step 3

Run the object detection model.

### Step 4

Extract detections.

Each detection should contain:

```json
{
  "class": "corrosion",
  "confidence": 0.91,
  "bounding_box": [x1, y1, x2, y2]
}
```

### Step 5

Generate an annotated image showing detected bounding boxes.

### Step 6

Calculate affected area.

---

# 10. Affected Area Calculation

For the prototype, calculate:

```text
affected_area_percentage =
total_area_of_corrosion_bounding_boxes /
image_area × 100
```

If multiple corrosion boxes overlap, avoid double-counting the overlapping area.

If exact segmentation is unavailable, clearly label this as an estimated affected area based on detection bounding boxes.

Do not pretend bounding-box area is exact physical corrosion surface area.

---

# 11. Severity Engine

The initial detection model does not inherently provide engineering severity.

Therefore implement a separate prototype severity engine.

Inputs:

- Corrosion affected area percentage
- Number of corrosion regions
- Detection confidence
- Environmental conditions

Output:

```text
Low
Moderate
High
Critical
```

Use configurable thresholds stored in configuration rather than hardcoding them throughout the application.

Example prototype configuration:

```text
LOW_MAX = configurable
MODERATE_MAX = configurable
HIGH_MAX = configurable
```

Do NOT claim these thresholds are industry standards.

Display a small UI note:

> Severity is a prototype estimate based on visual coverage and contextual factors. It is not a certified structural assessment.

The exact threshold values should be easy to change later.

---

# 12. Environmental Context

The DHT11 provides:

- Temperature
- Humidity

These values are contextual information.

The system must NOT claim that DHT11 alone predicts corrosion.

Use environmental data to modify inspection priority/context rather than pretending it is a corrosion predictor.

Example:

```text
Visual Result:
Corrosion detected
Severity: Moderate

Environment:
Temperature: 31.4°C
Humidity: 72%

Context:
Elevated humidity may increase maintenance priority.
```

Keep the environmental influence simple and transparent.

Do not train or claim an ML corrosion-risk model unless a suitable dataset actually exists.

---

# 13. Recommendation Engine

Create a deterministic recommendation engine.

Example mapping:

```text
No corrosion
→ Continue routine monitoring

Low
→ Monitor condition and schedule routine inspection

Moderate
→ Surface cleaning and protective coating inspection

High
→ Detailed maintenance inspection and repair assessment

Critical
→ Immediate professional structural/maintenance inspection
```

Recommendations are prototype guidance only.

Always include:

> AI-generated prototype guidance. Final maintenance decisions require qualified physical inspection.

The recommendation engine should be implemented as its own service so that it can later be replaced by a more advanced model.

---

# 14. Backend API

Implement these endpoints.

## Health

```http
GET /api/health
```

Response:

```json
{
  "status": "ok"
}
```

## Run inspection

```http
POST /api/inspection
```

Multipart/form-data:

```text
image
temperature
humidity
device_id
```

Return:

```json
{
  "inspection_id": "INS_001",
  "timestamp": "...",
  "detected": true,
  "detections": [
    {
      "class": "corrosion",
      "confidence": 0.91,
      "bounding_box": [100, 80, 350, 290]
    }
  ],
  "affected_area": 17.8,
  "severity": "Moderate",
  "temperature": 31.4,
  "humidity": 72,
  "recommendation": "Surface cleaning and protective coating inspection.",
  "annotated_image_url": "/uploads/..."
}
```

## Get inspection

```http
GET /api/inspection/{id}
```

## History

```http
GET /api/history
```

Support pagination.

## Statistics

```http
GET /api/statistics
```

Return dashboard statistics.

---

# 15. Database Model

Store:

```text
inspection_id
timestamp
image_reference
annotated_image_reference
device_id
temperature
humidity
detected
detections
detected_class
confidence
bounding_boxes
affected_area
severity
recommendation
```

The schema should be extensible.

---

# 16. Frontend Pages

Create these pages.

## `/`

Dashboard.

## `/inspect`

New inspection.

## `/inspection/[id]`

Detailed inspection result.

## `/history`

Inspection history.

---

# 17. Inspection Result UI

The result page should show:

### Original Image

Display uploaded image.

### AI Detection Image

Display annotated image with bounding boxes.

### Detection

```text
Corrosion Detected
Confidence: 91%
```

### Affected Area

```text
17.8%
```

### Severity

```text
MODERATE
```

### Environmental Data

```text
Temperature: 31.4°C
Humidity: 72%
```

### Recommendation

Display the generated maintenance recommendation.

### Disclaimer

Display:

> This result is a prototype AI-assisted inspection estimate and does not replace qualified physical inspection.

---

# 18. History Page

Display a table containing:

```text
Inspection ID
Date
Detection
Severity
Confidence
Temperature
Humidity
Device
```

Allow clicking an inspection to open the detailed result.

Add simple filtering by:

- Severity
- Detection status
- Date if practical

---

# 19. Dashboard Statistics

Implement backend statistics.

At minimum:

```text
Total Inspections
Corrosion Detected
No Corrosion
High/Critical Cases
Average Confidence
Average Affected Area
```

Display useful charts if easy to implement:

- Severity distribution
- Detection distribution
- Inspection timeline

Avoid spending excessive time on visualizations.

---

# 20. Hardware Integration Contract

The software must expose a clean interface for future hardware integration.

Hardware should eventually send:

```text
POST /api/inspection
```

with:

```text
image
temperature
humidity
device_id
```

The backend must process this exactly the same way as frontend uploads.

The software team does NOT need to implement the Arduino camera capture.

Hardware team responsibilities:

- Camera capture
- Sensor readings
- Sending image/data to API

Software responsibilities:

- API
- AI inference
- Severity
- Recommendations
- Storage
- Dashboard

---

# 21. Hardware Independence

Do NOT block the application because hardware is unavailable.

The application must run fully using:

- Local image uploads
- Sample corrosion images
- Manual sensor values

Create a `data/sample_images` directory and provide instructions for adding sample images.

If no model file is available initially, implement a clearly isolated mock/demo inference mode so the entire UI and API can be tested.

However, the mock mode must never be confused with real AI inference.

---

# 22. ML Model Integration Strategy

Build the inference service so that the model implementation is replaceable.

Example conceptual interface:

```python
class CorrosionDetector:
    def predict(self, image):
        ...
```

Possible implementations:

```text
Roboflow/YOLO detector
Mock detector
Future custom detector
```

Do not spread model-specific code throughout the backend.

The rest of the system should only depend on the detector interface.

---

# 23. Error Handling

Handle:

- Invalid image
- Missing image
- Corrupted image
- Model unavailable
- Database unavailable
- Invalid sensor values
- Unsupported image format
- Empty detection result
- Inference failure

Return useful HTTP errors.

Frontend should show human-readable messages.

Do not expose raw Python stack traces to users.

---

# 24. Input Validation

Temperature:

- Numeric
- Reasonable configurable range

Humidity:

- Numeric
- 0–100%

Image:

- Validate MIME type
- Validate extension
- Limit file size

Device ID:

- Optional
- Sanitized

---

# 25. Security Basics

Implement basic security appropriate for a college prototype:

- Validate uploaded files
- Restrict upload size
- Sanitize filenames
- Do not execute uploaded files
- Store uploads in controlled directories
- Use environment variables for configuration
- Never commit secrets
- Provide `.env.example`

No authentication system is required unless it can be added without slowing down the core project.

---

# 26. Environment Configuration

Create `.env.example`.

Example:

```env
MONGODB_URI=
DATABASE_NAME=corrosion_inspection

MODEL_PATH=
UPLOAD_DIR=uploads

LOW_MAX=
MODERATE_MAX=
HIGH_MAX=

NEXT_PUBLIC_API_URL=http://localhost:8000
```

Never hardcode credentials.

---

# 27. Local Development

The README must explain exactly how to run the project.

Backend:

```bash
cd backend
python -m venv venv
```

Windows activation:

```powershell
venv\Scripts\activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The README should clearly state the expected URLs.

Example:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
Swagger:  http://localhost:8000/docs
```

---

# 28. Demo Mode

Create a demo mode that allows the team to demonstrate the entire system quickly.

Demo flow:

```text
Open Dashboard
      ↓
Go to New Inspection
      ↓
Upload corrosion image
      ↓
Enter:
Temperature = 31.4
Humidity = 72
Device = CAM_001
      ↓
Run Inspection
      ↓
Show detection
      ↓
Show affected area
      ↓
Show severity
      ↓
Show environmental context
      ↓
Show recommendation
      ↓
Save inspection
      ↓
Open History
      ↓
Show stored inspection
```

This flow is the most important acceptance test.

---

# 29. UI Design Direction

Create a professional engineering/industrial inspection interface.

Style:

- Dark or dark-blue engineering dashboard
- Clean cards
- Clear severity indicators
- Technical but modern
- Responsive
- Minimal animations
- Good typography
- Clear visual hierarchy

Avoid:

- Excessive gradients
- Gaming-style UI
- Unnecessary animations
- Fake AI visual effects
- Huge amounts of text

The interface should look like an actual inspection/maintenance application.

---

# 30. Important Accuracy Rules

The implementation must respect these rules:

1. Do not claim the detection model directly predicts severity.
2. Do not claim DHT11 predicts corrosion.
3. Do not call prototype thresholds industry standards.
4. Do not claim AI replaces physical inspection.
5. Do not invent dataset labels.
6. Do not invent model accuracy.
7. Do not fabricate testing results.
8. Do not describe bounding-box area as exact physical corrosion area.
9. Clearly distinguish real model inference from demo/mock mode.
10. Keep environmental information as contextual data.

---

# 31. Testing Requirements

Create basic tests.

Backend tests should cover:

- Health endpoint
- Image validation
- Sensor validation
- Severity engine
- Recommendation engine
- Affected-area calculation
- Inspection creation
- Inspection retrieval

Test at least:

```text
No corrosion
Low
Moderate
High
Critical
```

Also test multiple bounding boxes.

Frontend should be manually tested for:

- Upload
- Loading state
- Error state
- Result display
- History
- Dashboard statistics

---

# 32. Acceptance Criteria

The project is considered complete when all of these work:

### Core

- [ ] Frontend starts
- [ ] Backend starts
- [ ] Database connects
- [ ] User can upload an image
- [ ] Backend receives image
- [ ] AI detector runs
- [ ] Detection result is returned
- [ ] Bounding boxes are displayed
- [ ] Affected area is calculated
- [ ] Severity is generated
- [ ] Temperature is stored
- [ ] Humidity is stored
- [ ] Recommendation is generated
- [ ] Inspection is stored
- [ ] History displays inspection
- [ ] Dashboard displays statistics

### Integration

- [ ] Hardware API contract is documented
- [ ] Hardware is not required for software demo
- [ ] Frontend and hardware can eventually use the same endpoint

### Quality

- [ ] No hardcoded secrets
- [ ] Environment variables documented
- [ ] Errors handled cleanly
- [ ] README is complete
- [ ] Basic tests pass
- [ ] Code is reasonably modular

---

# 33. Development Priority

The agent must prioritize in this exact order:

## Priority 1 — End-to-end pipeline

Make this work first:

```text
Upload
→ Backend
→ Model
→ Detection
→ Severity
→ Recommendation
→ Response
```

## Priority 2 — Persistence

```text
Response
→ Database
→ History
```

## Priority 3 — Frontend

```text
Dashboard
→ Inspection
→ Result
→ History
```

## Priority 4 — Polish

Only after the complete pipeline works:

- Better UI
- Charts
- Filtering
- Improved error messages
- Demo data
- Documentation

Do NOT spend time polishing the UI while the ML/backend pipeline is broken.

---

# 34. Agent Instructions

You are the implementation agent.

Work directly on the project.

Follow these rules:

1. Inspect the existing repository before creating files.
2. Reuse working code where possible.
3. Do not rewrite working components unnecessarily.
4. Implement the smallest working version first.
5. Test each layer before moving to the next.
6. Do not invent model capabilities.
7. Do not invent datasets.
8. Do not use paid APIs.
9. Prefer local/open-source inference.
10. Keep the hardware boundary modular.
11. Use clear type definitions.
12. Keep configuration centralized.
13. Add comments only where they explain non-obvious decisions.
14. Avoid unnecessary abstractions.
15. Do not add authentication unless necessary.
16. Do not add cloud infrastructure unless necessary.
17. Make local development easy.
18. Make the project demo-ready.
19. When something cannot be implemented because an external artifact is missing, isolate it behind an interface and provide a clearly labeled fallback/demo mode.
20. Never silently replace real ML inference with fake results.

---

# 35. Final Deliverables

The agent must produce:

```text
1. Working frontend
2. Working FastAPI backend
3. ML inference service
4. Severity engine
5. Recommendation engine
6. Database integration
7. Inspection history
8. Dashboard
9. Hardware API contract
10. Tests
11. README
12. .env.example
13. API documentation
```

The final project should be runnable locally with minimal setup.

---

# 36. Final End-to-End Demonstration

The final demonstration should look like:

```text
                    USER
                      │
                      ▼
              Upload Corrosion Image
                      │
                      ▼
                Next.js Frontend
                      │
                      ▼
                  FastAPI
                      │
             ┌────────┴────────┐
             ▼                 ▼
       Image Processing   Sensor Context
             │            Temp + Humidity
             ▼
       YOLO/Object Detector
             │
             ▼
      Corrosion Detection
             │
             ▼
      Affected Area %
             │
             ▼
       Severity Engine
             │
             ▼
   Recommendation Engine
             │
             ▼
          MongoDB
             │
             ▼
        Result Dashboard
             │
             ▼
        Inspection History
```

The final goal is a convincing, technically meaningful college engineering prototype demonstrating:

**AI-powered remote visual inspection of corrosion with environmental context, severity estimation, maintenance recommendations, inspection history, and a hardware-independent software architecture.**
