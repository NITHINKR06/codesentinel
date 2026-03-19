"use client"

interface Props {
  score: number
  label: string
}

export default function ScoreGauge({ score, label }: Props) {
  const color = score >= 80 ? "#1D9E75" : score >= 50 ? "#BA7517" : "#E24B4A"
  const r = 40
  const circumference = 2 * Math.PI * r
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#1F2937" strokeWidth="8" />
        <circle
          cx="50" cy="50" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
        <text x="50" y="50" textAnchor="middle" dominantBaseline="central"
          fill="white" fontSize="20" fontWeight="600">
          {score}
        </text>
      </svg>
      <span className="text-xs text-gray-500 mt-1">{label}</span>
    </div>
  )
}
