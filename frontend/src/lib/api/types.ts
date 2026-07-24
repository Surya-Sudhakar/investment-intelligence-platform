export interface HealthResponse {
  status: "healthy";
  service: string;
  version: string;
  timestamp: string;
}

export interface ReadyResponse {
  status: "ready";
  service: string;
  version: string;
  timestamp: string;
  application: "initialized";
  database: "connected";
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: unknown | null;
    request_id: string;
  };
}
