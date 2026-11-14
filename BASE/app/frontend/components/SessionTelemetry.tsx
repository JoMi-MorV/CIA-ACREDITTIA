"use client";

import { useEffect } from "react";
import { api, currentUser } from "@/lib/api";

const HEARTBEAT_MS = 60_000;
const IDLE_MS = 5 * 60_000;

export default function SessionTelemetry() {
  useEffect(() => {
    const user = currentUser();
    if (!user || user.role === "admin") return;

    let lastInteractionAt = 0;
    let sentHeartbeat = false;
    let reportingErrorLogged = false;

    const heartbeat = () => {
      if (document.visibilityState !== "visible"
          || !lastInteractionAt
          || Date.now() - lastInteractionAt > IDLE_MS) return;

      sentHeartbeat = true;
      void api("/auth/activity/heartbeat", { method: "POST" })
        .then(() => { reportingErrorLogged = false; })
        .catch((error: unknown) => {
          if (!reportingErrorLogged) {
            console.error("No se pudo registrar la actividad de la sesión.", error);
            reportingErrorLogged = true;
          }
        });
    };

    const recordInteraction = (event: Event) => {
      if (!event.isTrusted) return;
      lastInteractionAt = Date.now();
      if (!sentHeartbeat) heartbeat();
    };

    const interactionEvents = ["click", "keydown", "touchstart", "scroll"];
    interactionEvents.forEach((name) =>
      window.addEventListener(name, recordInteraction, { passive: true }));
    const timer = window.setInterval(heartbeat, HEARTBEAT_MS);

    return () => {
      interactionEvents.forEach((name) =>
        window.removeEventListener(name, recordInteraction));
      window.clearInterval(timer);
    };
  }, []);

  return null;
}
