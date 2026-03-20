"use client"
import { ScanEvent } from "@/types"
import { useRef, useEffect } from "react"

const STAGE_COLORS: Record<string, string> = {
  ingesting:   "text-blue-400",
  scanning:    "text-red-400",
  ghost_commit:"text-orange-400",
  chaining:    "text-yellow-400",
  generating:  "text-red-300",
  recon:       "text-purple-400",
  simulation:  "text-red-400",
  patching:    "text-blue-400",
  validating:  "text-green-400",
  profiling:   "text-purple-400",
  narrative:   "text-cyan-400",
  scoring:     "text-green-400",
  complete:    "text-green-300",
  failed:      "text-red-600",
  ping:        "hidden",
}

const STAGE_PREFIX: Record<string, string> = {
  ingesting:   "clone",
  scanning:    "scan ",
  ghost_commit:"git  ",
  chaining:    "graph",
  generating:  "poc  ",
  recon:       "recon",
  simulation:  "sim  ",
  patching:    "patch",
  validating:  "verify",
  profiling:   "intel",
  narrative:   "story",
  scoring:     "score",
  complete:    "done ",
  failed:      "ERROR",
}

export default function LiveFeed({ events }: { events: ScanEvent[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events])

  // Filter out ping events
  const visibleEvents = events.filter(e => e.stage !== "ping" && e.progress !== -1)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 h-72 overflow-y-auto font-mono text-xs">
      {/* Header line */}
      <div className="text-gray-600 mb-2 pb-2 border-b border-gray-800">
        CodeSentinel Red+Blue Agent — scan output
      </div>

      {visibleEvents.map((event, i) => {
        const color = STAGE_COLORS[event.stage] || "text-gray-500"
        if (color === "hidden") return null

        const prefix = STAGE_PREFIX[event.stage] || event.stage.padEnd(5)
        const data = event.data || {}

        // Build extra info from data fields
        let extra = ""
        if (data.count !== undefined) extra = `(${data.count})`
        else if (data.chains !== undefined) extra = `chains=${data.chains}`
        else if (data.before !== undefined && data.after !== undefined)
          extra = `${data.before}→${data.after}`
        else if (data.confirmed !== undefined)
          extra = data.confirmed ? "✓ confirmed" : "inconclusive"
        else if (data.secrets !== undefined) extra = `secrets=${data.secrets}`
        else if (data.endpoints !== undefined) extra = `endpoints=${data.endpoints}`

        return (
          <div key={i} className="flex gap-2 mb-1 leading-relaxed items-start">
            {/* Line number */}
            <span className="text-gray-700 shrink-0 select-none w-5 text-right">
              {i + 1}
            </span>

            {/* Timestamp-style progress */}
            <span className="text-gray-700 shrink-0">
              {String(event.progress).padStart(3)}%
            </span>

            {/* Stage prefix */}
            <span className={`shrink-0 ${color}`}>
              [{prefix}]
            </span>

            {/* Message */}
            <span className="text-gray-300 flex-1">{event.message}</span>

            {/* Extra data */}
            {extra && (
              <span className="text-gray-600 shrink-0 ml-auto">{extra}</span>
            )}
          </div>
        )
      })}

      {/* Blinking cursor */}
      {visibleEvents.length > 0 &&
        visibleEvents[visibleEvents.length - 1]?.stage !== "complete" &&
        visibleEvents[visibleEvents.length - 1]?.stage !== "failed" && (
        <div className="flex gap-2 mt-1">
          <span className="text-gray-700 w-5 text-right select-none">
            {visibleEvents.length + 1}
          </span>
          <span className="text-gray-700">  %</span>
          <span className="text-gray-500 animate-pulse">█</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}