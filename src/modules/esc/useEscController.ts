import { useEffect, useState } from "react";
import { escController } from "./escControllerInstance";
import type { EscState } from "./types";

export function useEscController() {
  const [state, setState] = useState<EscState>(
    escController.getState()
  );

  useEffect(() => {
    return escController.subscribe(setState);
  }, []);

  return {
    ...state,

    start: (minutes: number) =>
      escController.start(minutes),

    stop: () =>
      escController.stop(),

    toggle: (minutes: number) =>
      escController.toggle(minutes),

    runCheckIn: () =>
      escController.runCheckIn(),
  };
}