# Corrosion Inspection API — Reference

> **Base URL** `http://localhost:8000`  
> **Interactive docs** `http://localhost:8000/docs` (Swagger UI)  
> **ReDoc** `http://localhost:8000/redoc`

All endpoints return JSON. All timestamps are ISO 8601 UTC.

---

## Authentication

No authentication is required for this prototype.

---

## Endpoints

### Health

#### `GET /api/health`

Returns the current API and service status.

**Response `200 OK`**
```json
{
  "status": "ok",
  "inference_mode": "demo",
  "database": "sqlite",
  "model_available": true
}
```

| Field | Type | Description |
|---|---|---|
| `status` | string | Always `"ok"` when the service is running |
| `inference_mode` | `"real"` \| `"demo"` | `"demo"` = simulated detections; `"real"` = live YOLO model |
| `database` | `"sqlite"` \| `"mongodb"` | Active database backend |
| `model_available` | boolean | Whether a real model file was loaded |

---

### Run Inspection

#### `POST /api/inspection`

Execute a full corrosion inspection on an uploaded image.

**Content-Type** `multipart/form-data`

**Request fields**

| Field | Type | Required | Description |
|---|---|---|---|
| `image` | file | ✓ | Image file — JPG, PNG, or WEBP. Max 10 MB. |
| `temperature` | float | — | Ambient temperature in °C (−40 to 85) |
| `humidity` | float | — | Relative humidity % (0–100) |
| `device_id` | string | — | Optional device identifier (max 64 chars) |

**Response `201 Created`**
```json
{
  "inspection_id": "INS_E3C98844",
  "timestamp": "2026-09-23T14:31:00.123456+00:00",
  "device_id": "CAM_001",

  "detected": true,
  "detections": [
    {
      "class": "corrosion",
      "confidence": 0.91,
      "bounding_box": [100, 80, 350, 290]
    }
  ],
  "confidence": 0.91,

  "affected_area": 17.8,
  "severity": "Moderate",
  "severity_reasoning": "Affected area: 17.8%.",

  "temperature": 31.4,
  "humidity": 72.0,
  "environmental_note": "Elevated humidity (72%) may increase corrosion risk.",

  "recommendation": "Surface cleaning and protective coating inspection.",
  "recommendation_disclaimer": "AI-generated prototype guidance. Final maintenance decisions require qualified physical inspection.",

  "image_reference": "/uploads/abc123.jpg",
  "annotated_image_url": "/uploads/ann_def456.jpg",

  "inference_mode": "demo"
}
```

| Field | Type | Description |
|---|---|---|
| `inspection_id` | string | Unique identifier: `INS_` + 8-char hex |
| `detected` | boolean | Whether any defects were detected |
| `detections` | array | List of detection objects (see below) |
| `confidence` | float \| null | Highest confidence among all detections |
| `affected_area` | float | Estimated % of image area covered by defect bounding boxes. Bounding-box estimate only — not exact physical area |
| `severity` | `"Low"` \| `"Moderate"` \| `"High"` \| `"Critical"` | Prototype severity level |
| `environmental_note` | string | Contextual note about temperature/humidity |
| `inference_mode` | `"real"` \| `"demo"` | Always verify this field — `"demo"` means synthetic detections |

**Detection object**

```json
{
  "class": "corrosion",
  "confidence": 0.91,
  "bounding_box": [100, 80, 350, 290]
}
```

- `class` — one of `corrosion`, `crack`, `slippage` (from corrosion-bi3q3 model)
- `confidence` — 0.0–1.0
- `bounding_box` — `[x1, y1, x2, y2]` pixel coordinates

**Error responses**

| Status | Condition |
|---|---|
| `400` | Empty file |
| `422` | Unsupported file type, corrupt image, sensor values out of range |
| `500` | Unexpected server error |

---

### Get Inspection

#### `GET /api/inspection/{inspection_id}`

Retrieve a previously stored inspection by ID.

**Path parameter** `inspection_id` — e.g. `INS_E3C98844`

**Response `200 OK`** — same schema as POST response above.

**Response `404 Not Found`**
```json
{ "detail": "Inspection 'INS_UNKNOWN' not found." }
```

---

### Inspection History

#### `GET /api/history`

Return a paginated list of inspections.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 20 | Items per page (max 100) |
| `severity` | string | — | Filter: `Low`, `Moderate`, `High`, `Critical` |
| `detected` | boolean | — | Filter: `true` or `false` |
| `date_from` | string | — | ISO date lower bound (e.g. `2026-09-01`) |
| `date_to` | string | — | ISO date upper bound |

**Response `200 OK`**
```json
{
  "items": [ { "...inspection objects..." } ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

**Error `422`** if `severity` is not a valid level.

---

### Statistics

#### `GET /api/statistics`

Return aggregated statistics for the dashboard.

**Response `200 OK`**
```json
{
  "total_inspections": 42,
  "corrosion_detected": 35,
  "no_corrosion": 7,
  "high_critical_cases": 12,
  "critical_cases": 4,
  "detection_rate": 83.3,
  "avg_confidence": 0.814,
  "avg_affected_area": 18.5,
  "severity_distribution": {
    "Low": 5,
    "Moderate": 18,
    "High": 15,
    "Critical": 4
  },
  "inspection_timeline": [
    { "date": "2026-09-22", "count": 6 },
    { "date": "2026-09-23", "count": 12 }
  ]
}
```

---

## Static Files

Uploaded and annotated images are served as static files:

```
GET /uploads/{filename}
```

The `image_reference` and `annotated_image_url` fields in inspection responses contain paths relative to the API base URL, e.g. `/uploads/abc123.jpg`.

---

## Hardware Integration Contract

The backend is hardware-agnostic. Any device can submit an inspection by sending:

```
POST /api/inspection
Content-Type: multipart/form-data

image       = <image bytes>
temperature = <float>
humidity    = <float>
device_id   = <string>
```

This is identical to the frontend browser upload. No separate endpoint is needed for hardware devices.

**Hardware team responsibilities:**
- Capture image (OV7670, ESP32-CAM, RPi camera, etc.)
- Read DHT11 or equivalent sensor
- Send multipart POST to `/api/inspection`
- Optionally poll `GET /api/inspection/{id}` for the result

**Software team responsibilities:**
- All processing described above
- No Arduino or embedded code required

---

## Severity Levels

> ⚠ These thresholds are **prototype estimates** and are **not** certified engineering standards.

| Level | Default affected area threshold | Meaning |
|---|---|---|
| Low | ≤ 5% | Minor indicators — routine monitoring |
| Moderate | 5–20% | Notable corrosion — schedule maintenance |
| High | 20–50% | Significant corrosion — prioritise repair |
| Critical | > 50% | Severe corrosion — immediate inspection |

Thresholds are configurable via `.env` (`LOW_MAX`, `MODERATE_MAX`, `HIGH_MAX`).

Secondary factors (number of regions, environmental conditions) can promote severity by one level when multiple signals concur.

---

## Environmental Context

Temperature and humidity data from DHT11 (or manual entry) are **contextual only**.
The system does **not** claim that sensor readings alone predict corrosion.
Environmental data modifies inspection priority notes and can contribute to severity promotion.
