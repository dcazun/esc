import { getDatabase } from "../Database";
import type { Session } from "../../src/modules/esc/types";

export async function saveSession(session: Session): Promise<void> {
  const db= await getDatabase();

  await db.execute(
    `
      INSERT INTO sessions (
        id,
        date,
        start_time,
        end_time,
        length_seconds
      )
      VALUES (?, ?, ?, ?, ?)
    `,
    [
      session.id,
      session.date,
      session.startTime,
      session.endTime,
      session.lengthSeconds,
    ]
  );
}

export async function getSessionsBetween(startDate: string, endDate: string): Promise<Session[]> {
  const db = await getDatabase();

  const sessions = await db.select<Session[]>(
    `
      SELECT
        id,
        date,
        start_time AS startTime,
        end_time AS endTime,
        length_seconds AS lengthSeconds
      FROM sessions
      WHERE date BETWEEN ? and ?
      ORDER BY date, start_time;    
    `,
    [
      startDate,
      endDate,
    ]
  );
  
  return sessions;
}