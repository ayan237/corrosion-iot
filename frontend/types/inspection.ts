// Shared TypeScript types for the Corrosion Inspection system.
// These mirror the FastAPI response schemas exactly.

export interface Detection {
  class: string;
  confidence: number;
  bounding_box: [number, number, number, number];
}

export type SeverityLevel = "Low" | "Moderate" | "High" | "Critical";

export interface AISolution {
  summary: string;
  immediate_actions?: string[];
  surface_preparation?: string[];
  treatment_and_coating?: string[];
  preventive_schedule?: string;
  estimated_urgency?: string;
  model_used?: string;
}

export interface Inspection {
  inspection_id: string;
  timestamp: string;
  device_id?: string | null;

  // Detection
  detected: boolean;
  detections: Detection[];
  confidence?: number | null;

  // Area + severity
  affected_area: number;
  severity: SeverityLevel | null;
  severity_reasoning?: string;

  // Environment
  temperature?: number | null;
  humidity?: number | null;
  environmental_note?: string;

  // Recommendation
  recommendation: string;
  recommendation_disclaimer?: string;
  ai_solution?: AISolution | null;

  // Files
  image_reference?: string | null;
  annotated_image_url?: string | null;

  // Meta
  inference_mode: "real" | "demo";
}

export interface HistoryResponse {
  items: Inspection[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Statistics {
  total_inspections: number;
  corrosion_detected: number;
  no_corrosion: number;
  high_critical_cases: number;
  critical_cases: number;
  detection_rate: number;
  avg_confidence: number;
  avg_affected_area: number;
  severity_distribution: Record<string, number>;
  inspection_timeline: { date: string; count: number }[];
}

export interface HealthStatus {
  status: string;
  inference_mode: "real" | "demo";
  database: string;
  model_available: boolean;
}
