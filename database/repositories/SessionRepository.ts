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