"use client"
import { useEffect, useState, useRef } from "react"
import { useRouter, useParams } from "next/navigation"
import { connectToScan } from "@/lib/socket"
import { ScanEvent } from "@/types"

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

  const circleRadius = 104
  const circumference = 2 * Math.PI * circleRadius
  const dashOffset = ((100 - progress) / 100) * circumference

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
    return () => {
      if (ws.readyState === 1) {
        ws.close()
      } else {
        ws.addEventListener('open', () => ws.close())
      }
    }
  }, [scanId, router])

  const handleStopScan = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
      await fetch(`${API_URL}/scan/${scanId}/cancel`, { method: 'POST' })
    } catch (e) {
      console.error("Failed to stop scan", e)
    }
    router.push("/dashboard")
  }

  return (
    <main className="bg-background text-on-surface font-body selection:bg-primary selection:text-on-primary min-h-screen">
      <div className="flex h-screen overflow-hidden">
        {/* SideNav */}
        <aside className="bg-surface-container-low w-64 flex flex-col h-full border-r border-outline/15 shadow-[4px_0_24px_rgba(152,203,255,0.05)] hidden lg:flex">
          <div className="p-6 border-b border-outline/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-sm bg-surface-container-high border border-outline-variant/30 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary">security</span>
              </div>
              <div>
                <h2 className="font-headline font-bold text-sm text-primary tracking-tight">CodeSentinel Ops</h2>
                <p className="font-mono text-[10px] opacity-60 uppercase tracking-widest text-on-surface">Level 4 Clearance</p>
              </div>
            </div>
          </div>
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto text-xs font-semibold uppercase tracking-widest">
            <p className="text-[10px] text-on-surface opacity-40 px-2 mb-3">Core Modules</p>
            {[
              { label: "Dashboard", icon: "dashboard" },
              { label: "Active Scans", icon: "radar" },
              { label: "Red Team Reports", icon: "security" },
              { label: "Blue Team Reports", icon: "shield" },
              { label: "Settings", icon: "settings" },
            ].map(item => (
              <div
                key={item.label}
                className={`flex items-center gap-3 px-4 py-3 rounded-sm transition-all ${
                  item.label === "Active Scans"
                    ? "bg-[#2A2A2A] text-primary border-l-4 border-primary"
                    : "text-on-surface/70 hover:bg-[#201F1F] hover:text-on-surface"
                }`}
              >
                <span className="material-symbols-outlined text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </nav>
          <div className="p-4 border-t border-outline/10 bg-[#131313] text-xs uppercase tracking-widest font-semibold">
            <div className="space-y-1">
              <div className="flex items-center gap-3 px-4 py-2 text-on-surface/70 hover:bg-[#201F1F] hover:text-on-surface transition-all">
                <span className="material-symbols-outlined text-base">help_center</span>
                <span>Support</span>
              </div>
              <div className="flex items-center gap-3 px-4 py-2 text-on-surface/70 hover:bg-[#201F1F] hover:text-on-surface transition-all">
                <span className="material-symbols-outlined text-base">terminal</span>
                <span>Logs</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main column */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top bar */}
          <header className="bg-[#131313] flex justify-between items-center w-full px-6 py-3 h-16 border-b border-outline/10">
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-bold tracking-tighter text-primary font-headline">CodeSentinel</h1>
              <div className="hidden lg:flex items-center gap-6 font-headline text-sm tracking-tight">
                <span className="text-primary font-bold border-b-2 border-primary py-1">Active Scan</span>
                <span className="text-on-surface/70 hover:bg-[#2A2A2A] hover:text-primary px-3 py-1 rounded transition-colors">
                  Vulnerability DB
                </span>
                <span className="text-on-surface/70 hover:bg-[#2A2A2A] hover:text-primary px-3 py-1 rounded transition-colors">
                  CI/CD Integration
                </span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative bg-surface-container-low rounded-sm px-3 py-1.5 flex items-center gap-2">
                <span className="material-symbols-outlined text-outline text-sm">search</span>
                <input
                  className="bg-transparent border-none focus:ring-0 text-xs text-on-surface w-48 placeholder:opacity-40"
                  placeholder="Search resources..."
                  type="text"
                />
              </div>
              <button className="w-10 h-10 flex items-center justify-center rounded hover:bg-[#2A2A2A] text-on-surface/80 transition-colors" type="button">
                <span className="material-symbols-outlined">sensors</span>
              </button>
              <button className="w-10 h-10 flex items-center justify-center rounded hover:bg-[#2A2A2A] text-on-surface/80 transition-colors" type="button">
                <span className="material-symbols-outlined">account_circle</span>
              </button>
              {!done && currentStage !== "failed" && (
                <button
                  onClick={handleStopScan}
                  className="px-3 py-1.5 bg-error-container/10 hover:bg-error-container/30 text-secondary border border-error-container/60 rounded text-xs font-mono uppercase tracking-widest"
                  type="button"
                >
                  Stop Scan
                </button>
              )}
            </div>
          </header>

          {/* Content grid */}
          <div className="flex-1 overflow-hidden p-6 bg-background grid grid-cols-12 gap-6">
            {/* Left column: target + pipeline */}
            <div className="col-span-12 lg:col-span-3 space-y-6">
              <div className="bg-surface-container-low p-6 rounded border-l-2 border-primary/40">
                <h3 className="font-headline font-bold text-xs uppercase tracking-widest text-on-surface/60 mb-6">
                  Target Identity
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] text-primary uppercase font-mono mb-1">Repository</p>
                    <p className="text-on-surface font-mono font-medium text-sm break-all">{scanId}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-primary uppercase font-mono mb-1">Active Branch</p>
                    <p className="text-on-surface font-mono font-medium text-sm flex items-center gap-2">
                      <span className="material-symbols-outlined text-xs">fork_right</span>
                      production
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-surface-container p-4 rounded">
                <h3 className="font-headline font-bold text-xs uppercase tracking-widest text-on-surface/60 mb-6 px-2">
                  Pipeline Execution
                </h3>
                <div className="space-y-1 text-xs font-sans">
                  <div className="flex items-center gap-4 px-4 py-3 bg-surface-container-low rounded border-l-2 border-tertiary">
                    <span className="material-symbols-outlined text-tertiary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                      check_circle
                    </span>
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-on-surface">Ingesting</p>
                      <p className="text-[10px] font-mono opacity-50 uppercase">Success</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 px-4 py-3 bg-surface-container-low rounded border-l-2 border-tertiary">
                    <span className="material-symbols-outlined text-tertiary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                      check_circle
                    </span>
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-on-surface">Static Analysis</p>
                      <p className="text-[10px] font-mono opacity-50 uppercase">Success</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 px-4 py-3 bg-surface-container-high rounded border-l-4 border-primary">
                    <span className="material-symbols-outlined text-primary text-lg animate-pulse">radar</span>
                    <div className="flex-1">
                      <p className="text-xs font-bold text-primary">{STAGE_LABELS[currentStage] || currentStage}</p>
                      <p className="text-[10px] font-mono text-primary/70 uppercase">Executing exploit path</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 px-4 py-3 opacity-40 grayscale">
                    <span className="material-symbols-outlined text-on-surface text-lg">shield</span>
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-on-surface">Auto Patching</p>
                      <p className="text-[10px] font-mono opacity-50 uppercase">Pending</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right column: progress + logs */}
            <div className="col-span-12 lg:col-span-9 flex flex-col gap-6">
              {/* Progress card */}
              <div className="bg-surface-container-low rounded p-12 flex flex-col items-center justify-center relative overflow-hidden border border-outline-variant/10">
                <div className="absolute inset-0 opacity-10 pointer-events-none">
                  <div className="absolute -top-1/4 -right-1/4 w-96 h-96 bg-primary blur-[120px] rounded-full" />
                  <div className="absolute -bottom-1/4 -left-1/4 w-96 h-96 bg-secondary blur-[120px] rounded-full" />
                </div>

                <div className="relative z-10 text-center">
                  <h2 className="font-headline font-bold text-primary text-[10px] uppercase tracking-[0.4em] mb-8">
                    System Threat Extraction In-Progress
                  </h2>

                  <div className="relative w-64 h-64 mx-auto mb-8 flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border border-primary/20 animate-ping" style={{ animationDuration: "3s" }} />
                    <div className="absolute inset-4 rounded-full border border-primary/30" />
                    <svg className="w-56 h-56 transform -rotate-90 drop-shadow-[0_0_15px_rgba(152,203,255,0.4)]">
                      <circle
                        className="text-surface-container-high"
                        cx="112"
                        cy="112"
                        r={circleRadius}
                        fill="transparent"
                        stroke="currentColor"
                        strokeWidth="2"
                      />
                      <circle
                        className="text-primary transition-all duration-500"
                        cx="112"
                        cy="112"
                        r={circleRadius}
                        fill="transparent"
                        stroke="currentColor"
                        strokeWidth="8"
                        strokeDasharray={circumference}
                        strokeDashoffset={dashOffset}
                        strokeLinecap="square"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="font-headline text-7xl font-extrabold text-on-surface tracking-tighter">
                        {progress}
                        <span className="text-2xl text-primary font-mono">%</span>
                      </span>
                      <span className="text-[10px] font-mono text-primary/70 uppercase tracking-widest mt-2">
                        Analysis Index
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <h3 className="text-2xl font-headline font-bold text-secondary tracking-tight">
                      CHAINING VULNERABILITIES...
                    </h3>
                    <p className="text-xs text-on-surface-variant font-mono uppercase tracking-widest">
                      Complex exploit tree reconstruction
                    </p>
                  </div>
                </div>

                <div className="mt-12 grid grid-cols-3 gap-12 border-t border-outline-variant/15 pt-12 w-full max-w-2xl">
                  <div className="text-center">
                    <p className="text-on-surface-variant text-[10px] uppercase font-mono mb-1">Critical Hits</p>
                    <p className="text-secondary text-2xl font-headline font-bold">
                      {events.filter(e => e.stage === "scoring" || e.stage === "chaining").length || 0}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-on-surface-variant text-[10px] uppercase font-mono mb-1">Time Elapsed</p>
                    <p className="text-on-surface text-2xl font-headline font-bold">--:--</p>
                  </div>
                  <div className="text-center">
                    <p className="text-on-surface-variant text-[10px] uppercase font-mono mb-1">Events</p>
                    <p className="text-tertiary text-2xl font-headline font-bold">{events.length}</p>
                  </div>
                </div>
              </div>

              {/* Logs */}
              <div className="flex-1 min-h-[300px] flex flex-col bg-surface-container-lowest border border-outline-variant/20 rounded overflow-hidden">
                <div className="bg-surface-container-high px-4 py-2 flex items-center justify-between border-b border-outline-variant/30">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1.5 mr-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-secondary/60" />
                      <div className="w-2.5 h-2.5 rounded-full bg-primary/60" />
                      <div className="w-2.5 h-2.5 rounded-full bg-tertiary/60" />
                    </div>
                    <p className="font-mono text-[10px] uppercase tracking-widest text-on-surface/50 font-bold">
                      Live System Logs :: node-cs-scanner-04
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 font-mono text-[10px] text-tertiary">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-tertiary" />
                      </span>
                      LIVE STREAM
                    </span>
                    <span className="material-symbols-outlined text-on-surface/40 text-sm">settings_input_component</span>
                  </div>
                </div>
                <div className="flex-1 p-4 font-mono text-xs overflow-y-auto space-y-1.5">
                  {events.map((event, i) => (
                    <div
                      key={i}
                      className={`flex gap-4 group ${
                        event.stage === "ghost_commit" || event.stage === "chaining"
                          ? "bg-secondary/5 -mx-4 px-4 border-l-2 border-secondary"
                          : ""
                      }`}
                    >
                      <span className="text-outline-variant shrink-0">
                        {new Date(event.timestamp || Date.now()).toLocaleTimeString("en-US", { hour12: false })}
                      </span>
                      <span className={`shrink-0 w-12 uppercase tracking-tighter ${STAGE_COLORS[event.stage] || "text-primary"}`}>
                        [{STAGE_LABELS[event.stage] || event.stage}]
                      </span>
                      <span className="text-on-surface-variant flex-1">{event.message}</span>
                      {event.data && Object.keys(event.data).length > 0 && (
                        <span className="text-on-surface-variant/60 ml-auto shrink-0">
                          {Object.entries(event.data)
                            .map(([k, v]) => `${k}:${v}`)
                            .join(" ")}
                        </span>
                      )}
                    </div>
                  ))}
                  {!done && (
                    <div className="flex gap-4 group">
                      <span className="text-outline-variant shrink-0">--:--:--</span>
                      <span className="text-primary shrink-0 w-12 uppercase tracking-tighter">[RUN]</span>
                      <span className="text-primary animate-pulse">Execution pending next event...</span>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              </div>

              {done && (
                <div className="text-center text-tertiary text-sm animate-pulse font-mono">
                  Scan complete — loading report...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
