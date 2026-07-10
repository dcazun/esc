import { useEffect } from "react";
import { load } from "@tauri-apps/plugin-store";
import {
  enable,
  disable,
  isEnabled,
} from "@tauri-apps/plugin-autostart";

import { Shell } from "./Shell";
import NudgeWindow from "./views/NudgeWindow";
import { escController } from "./modules/esc/escControllerInstance";

import "./App.css";

const DEFAULT_SETTINGS = {
  automaticMode: true,
  checkInTimer: 5,
  runAtStartup: true,
};

function App() {
  const isNudge =
    window.location.pathname === "/nudge" ||
    window.location.search.includes("confidence");

  useEffect(() => {
    // Do not initialize monitoring from the separate nudge window.
    if (isNudge) {
      return;
    }

    async function initializeApp() {
      const store = await load("settings.json", {
        autoSave: true,
        defaults: {
          automaticMode: DEFAULT_SETTINGS.automaticMode,
          checkInTimer: DEFAULT_SETTINGS.checkInTimer,
          runAtStartup: DEFAULT_SETTINGS.runAtStartup,
        },
      });

      const automaticMode =
        await store.get<boolean>("automaticMode");

      const checkInTimer =
        await store.get<number>("checkInTimer");

      const runAtStartup =
        await store.get<boolean>("runAtStartup");

      /*
       * runAtStartup controls whether the operating system
       * launches ESC when the user logs in.
       */
      const autostartEnabled = await isEnabled();

      if (runAtStartup === true && !autostartEnabled) {
        await enable();
      } else if (runAtStartup === false && autostartEnabled) {
        await disable();
      }

      /*
       * automaticMode controls whether ESC monitoring starts
       * once the application itself has launched.
       */
      if (automaticMode === true) {
        await escController.start(
          checkInTimer ?? DEFAULT_SETTINGS.checkInTimer
        );
      }
    }

    void initializeApp();
  }, [isNudge]);

  if (isNudge) {
    const confidence = parseFloat(
      new URLSearchParams(window.location.search).get("confidence") || "0"
    );

    return <NudgeWindow confidence={confidence} />;
  }

  return <Shell />;
}

export default App;