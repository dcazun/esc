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

export interface Session {
  id: string;
  date: string;
  startTime: string;
  endTime: string | null;
  lengthSeconds: number | null;
}