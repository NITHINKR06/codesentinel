"use client"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"

interface DataPoint {
  label: string
  score: number
}

export default function ScoreHistory({ data }: { data: DataPoint[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="text-sm font-medium text-gray-300 mb-4">Security score history</div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
          <XAxis dataKey="label" tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
            labelStyle={{ color: "#9CA3AF", fontSize: 11 }}
            itemStyle={{ color: "#1D9E75", fontSize: 12 }}
          />
          <Line
            type="monotone" dataKey="score"
            stroke="#1D9E75" strokeWidth={2}
            dot={{ fill: "#1D9E75", r: 4 }}
            activeDot={{ r: 6, fill: "#34D399" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
