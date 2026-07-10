import { invoke } from "@tauri-apps/api/core";
import type { DetectionResult, EscState } from "./types";

type StateListener = (state: EscState) => void;

export class EscController {
  private intervalId: ReturnType<typeof setInterval> | null = null;

  private state: EscState = {
    isRunning: false,
    isChecking: false,
    status: "Not running",
    error: "",
  };

  private listeners = new Set<StateListener>();

  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);

    // Immediately giev the subscriber to the current state.
    listener(this.state);

    return () => {
      this.listeners.delete(listener);
    };
  }

  private updateState(changes: Partial<EscState>): void {
    this.state = {
      ...this.state,
      ...changes,
    };

    for (const listener of this.listeners) {
      listener(this.state);
    }
  }

  getState(): EscState {
    return this.state;
  }

  async start(minutes: number): Promise<void> {
    if (this.state.isRunning) {
      return;
    }

    this.updateState({
      isRunning: true,
      status: "Monitoring started...",
      error: "",
    });

    this.intervalId = setInterval(() => {
      void this.runCheckIn();
    }, minutes * 60 * 1000);
  }

  async stop(): Promise<void> {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    this.updateState({
      isRunning: false,
      isChecking: false,
      status: "Not running",
    });

    try {
      await invoke("stop_detector");
    } catch {
      // Detector was already stopped.
    }
  }

  async toggle(minutes: number): Promise<void> {
    if (this.state.isRunning) {
      await this.stop();
    } else {
      await this.start(minutes);
    }
  }

  async runCheckIn(): Promise<void> {
    if (this.state.isChecking) {
      return;
    }

    this.updateState({
      isChecking: true,
      status: "Analyzing posture...",
      error: "",
    });

    try {
      const result =
        await invoke<DetectionResult>("start_detector");

      if (result.distracted) {
        this.updateState({
          isChecking: false,
          status:
            `Distracted! (confidence: ${
              (result.confidence * 100).toFixed(0)
            }%)`,
        });

        await invoke("show_nudge", {
          confidence: result.confidence,
        });
      } else {
        this.updateState({
          isChecking: false,
          status:
            `Focused! (confidence: ${
              (100 - result.confidence * 100).toFixed(0)
            }%)`,
        });
      }

      setTimeout(() => {
        if (this.state.isRunning) {
          this.updateState({
            status: "Monitoring...",
          });
        }
      }, 5000);
    } catch (error) {
      await this.stop();

      this.updateState({
        error: String(error),
      });
    }
  }

}