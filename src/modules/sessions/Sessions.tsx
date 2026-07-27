import { getCurrentWeekSummary, type DaySummary } from "../../../database/repositories/SessionSummary";
import { useEffect, useState } from "react"; 
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function Sessions() {
  const [summary, setSummary] = useState<DaySummary[]>([]);

  useEffect(() => {
    async function loadSummary() {
    try {
      const weekSummary = await getCurrentWeekSummary();

      console.log("Current week summary:", weekSummary);

      setSummary(weekSummary);
    } catch (error) {
      console.error("Failed to get session summary:", error);
    }
  }
    loadSummary();
  }, []);

  return (
    <div>
      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={summary}>
            <XAxis dataKey="dayLabel" />

            <YAxis />
            
            <Tooltip />

            <Bar dataKey="totalMinutes" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default Sessions;