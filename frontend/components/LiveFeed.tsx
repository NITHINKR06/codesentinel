"use client"
import { ScanEvent } from "@/types"
import { useRef, useEffect } from "react"

const STAGE_COLORS: Record<string, string> = {
  ingesting: "text-blue-400",
  scanning: "text-red-400",
  ghost_commit: "text-orange-400",
  chaining: "text-red-400",
  generating: "text-orange-400",
  patching: "text-blue-400",
  validating: "text-green-400",
  profiling: "text-purple-400",
  scoring: "text-green-400",
  complete: "text-green-300",
  failed: "text-red-600",
}

export default function LiveFeed({ events }: { events: ScanEvent[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events])

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 h-64 overflow-y-auto font-mono text-xs">
      {events.map((event, i) => (
        <div key={i} className="flex gap-3 mb-1.5 leading-relaxed">
          <span className="text-gray-700 shrink-0 select-none">{String(i + 1).padStart(2, "0")}</span>
          <span className={`shrink-0 ${STAGE_COLORS[event.stage] || "text-gray-500"}`}>
            [{event.stage}]
          </span>
          <span className="text-gray-300 flex-1">{event.message}</span>
          {event.progress > 0 && (
            <span className="text-gray-600 shrink-0">{event.progress}%</span>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
