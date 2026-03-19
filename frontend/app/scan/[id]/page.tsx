"use client"
import { useEffect, useState, useRef } from "react"
import { useRouter, useParams } from "next/navigation"
import { connectToScan } from "@/lib/socket"
import { ScanEvent } from "@/types"
import { Shield, ChevronRight } from "lucide-react"

const STAGE_LABELS: Record<string, string> = {
  ingesting: "Cloning repository",
  scanning: "AST vulnerability scan",
  ghost_commit: "Git history scan",
  chaining: "Building call graph",
  generating: "Generating PoC exploits",
  patching: "Writing security patches",
  validating: "Red agent validating patches",
  profiling: "Threat actor profiling",
  scoring: "Calculating security score",
  complete: "Complete",
  failed: "Failed",
}

const STAGE_COLORS: Record<string, string> = {
  ingesting: "text-blue-400",
  scanning: "text-red-400",
  ghost_commit: "text-orange-400",
  chaining: "text-red-400",
  generating: "text-red-400",
  patching: "text-blue-400",
  validating: "text-green-400",
  profiling: "text-purple-400",
  scoring: "text-green-400",
  complete: "text-green-400",
  failed: "text-red-600",
}

export default function ScanPage() {
  const params = useParams()
  const scanId = params.id as string
  const router = useRouter()
  const [events, setEvents] = useState<ScanEvent[]>([])
  const [progress, setProgress] = useState(0)
  const [currentStage, setCurrentStage] = useState("ingesting")
  const [done, setDone] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ws = connectToScan(
      scanId,
      (event) => {
        setEvents(prev => [...prev, event])
        setProgress(event.progress)
        setCurrentStage(event.stage)
        bottomRef.current?.scrollIntoView({ behavior: "smooth" })
      },
      () => {
        setDone(true)
        setTimeout(() => router.push(`/scan/${scanId}/report`), 1500)
      },
      () => setCurrentStage("failed")
    )
    return () => ws.close()
  }, [scanId, router])

  return (
    <main className="min-h-screen bg-gray-950 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <Shield className="w-7 h-7 text-red-400" />
          <h1 className="text-xl font-semibold text-white">CodeSentinel</h1>
          <ChevronRight className="w-4 h-4 text-gray-600" />
          <span className="text-gray-400 text-sm font-mono">{scanId.slice(0, 8)}...</span>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm mb-2">
            <span className={`font-medium ${STAGE_COLORS[currentStage] || "text-gray-400"}`}>
              {STAGE_LABELS[currentStage] || currentStage}
            </span>
            <span className="text-gray-500">{progress}%</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-600 to-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Terminal feed */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 h-80 overflow-y-auto font-mono text-xs">
          {events.map((event, i) => (
            <div key={i} className="flex gap-3 mb-1.5">
              <span className="text-gray-600 shrink-0">{String(i + 1).padStart(2, "0")}</span>
              <span className={`shrink-0 ${STAGE_COLORS[event.stage] || "text-gray-500"}`}>
                [{STAGE_LABELS[event.stage] || event.stage}]
              </span>
              <span className="text-gray-300">{event.message}</span>
              {event.data && Object.keys(event.data).length > 0 && (
                <span className="text-gray-600 ml-auto shrink-0">
                  {Object.entries(event.data).map(([k, v]) => `${k}:${v}`).join(" ")}
                </span>
              )}
            </div>
          ))}
          {!done && (
            <div className="flex gap-3 mt-1">
              <span className="text-gray-600">--</span>
              <span className="text-gray-500 animate-pulse">█</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {done && (
          <div className="mt-6 text-center text-green-400 text-sm animate-pulse">
            Scan complete — loading report...
          </div>
        )}
      </div>
    </main>
  )
}
