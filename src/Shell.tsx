import { useState } from "react";
import Home from "./views/Home";
import Settings from "./views/Settings";

export type View = "home" | "settings";

function Shell() {
  const [view, setView] = useState<View>("home");

  function navigate(to: View) {
    setView(to);
  }

  return (
    <>
      {view === "home" && <Home onNavigate={navigate} />}
      {view === "settings" && <Settings onNavigate={navigate} />}
    </>
  );
}
export { Shell };