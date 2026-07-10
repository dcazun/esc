export interface DetectionResult {
  distracted: boolean;
  confidence: number;
}

export interface EscState {
  isRunning: boolean;
  isChecking: boolean;
  status: string;
  error: string;
}