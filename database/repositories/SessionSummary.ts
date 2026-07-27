import type { Session } from "../../src/modules/esc/types";
import { getSessionsBetween } from "./SessionRepository";

export interface DaySummary {
  dayLabel: string;
  date: string;
  isToday: boolean;
  sessionCount: number;
  totalMinutes: number;
}

export async function getCurrentWeekSummary(): Promise<DaySummary[]> {
  const week = getCurrentWeek();

  const startDate = week[0].date;
  const endDate = week[6].date;

  const sessions = await getSessionsBetween(
    startDate,
    endDate
  );

  return summarizeSessions(sessions, week);
}

export function getCurrentWeek(): DaySummary[] {
  // Organize week's range
  const today = new Date();
  const dayIndex = today.getDay();

  const sunday = new Date(today);
  sunday.setDate(today.getDate() - dayIndex);

  const days: DaySummary[] = [];

  for (let i = 0; i < 7; i++) {
    const date = new Date(sunday);
    date.setDate(date.getDate() + i);

    days.push({
      dayLabel: date.toLocaleDateString("en-US", {
        weekday: "short",
      }),
      date: date.toLocaleDateString("en-CA"),
      isToday:
        date.toLocaleDateString("en-CA") ===
        today.toLocaleDateString("en-CA"),
      sessionCount: 0,
      totalMinutes: 0,
    });
  }

  return days;
}

export function summarizeSessions( 
  sessions: Session[],
  week: DaySummary[],
): DaySummary[] {
  
  for (const session of sessions) {
    const day = week.find(
      (entry) => entry.date === session.date
    );

    if (!day || session.lengthSeconds === null) {
      continue;
    }

    day.sessionCount += 1;
    day.totalMinutes += session.lengthSeconds / 60;
  }

  return week;
}