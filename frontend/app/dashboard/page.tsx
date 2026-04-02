"use client"
import { useEffect, useState } from "react"
import Link from "next/link"
import { listScans } from "@/lib/api"
import { Shield, ExternalLink, Clock } from "lucide-react"
import ScoreHistory from "@/components/ScoreHistory"
import OpsSidebar from "@/components/OpsSidebar"

interface ScanSummary {
  scan_id: string
  status: string
  repo_name?: string
  github_url?: string
  score_before?: number
  score_after?: number
  total_findings: number
  created_at?: string
}

export default function DashboardPage() {
  const [scans, setScans] = useState<ScanSummary[]>([])

  useEffect(() => {
    listScans().then(setScans)
  }, [])

  const scoreHistory = scans
    .filter(s => s.score_after != null)
    .slice(0, 10)
    .reverse()
    .map(s => ({
      label: (s.repo_name || s.scan_id.slice(0, 8)).split("/").pop() || s.scan_id.slice(0, 8),
      score: s.score_after!,
    }))

  const STATUS_STYLES: Record<string, string> = {
    complete: "text-green-400 bg-green-900/20 border-green-800",
    failed: "text-red-400 bg-red-900/20 border-red-800",
    pending: "text-gray-400 bg-gray-800 border-gray-700",
    scanning: "text-blue-400 bg-blue-900/20 border-blue-800",
  }

  return (
    <main className="bg-background text-on-background font-[Inter] min-h-screen overflow-hidden flex flex-col">
      {/* Top nav aligned with scan theme */}
      <header className="bg-[#131313] text-[#98CBFF] font-['Space_Grotesk'] text-sm tracking-tight fixed top-0 w-full flex justify-between items-center px-6 py-3 h-16 z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-[#98CBFF]">CodeSentinel</span>
          <nav className="hidden md:flex gap-6 items-center">
            <span className="text-[#98CBFF] font-bold border-b-2 border-[#98CBFF] px-2 py-1">Dashboard</span>
            <Link
              href="/telemetry"
              className="text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors px-2 py-1 rounded-sm"
            >
              Telemetry
            </Link>
            <Link
              href="/threat-map"
              className="text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors px-2 py-1 rounded-sm"
            >
              Threat Map
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden sm:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
            <input
              className="bg-[#1c1b1b] border-none text-xs w-64 pl-10 pr-4 py-2 rounded-sm focus:ring-1 focus:ring-primary font-mono"
              placeholder="Global Identifier Search..."
              type="text"
            />
          </div>
          <div className="flex gap-2">
            <button className="p-2 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors rounded-sm" type="button">
              <span className="material-symbols-outlined">sensors</span>
            </button>
            <button className="p-2 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors rounded-sm" type="button">
              <span className="material-symbols-outlined">account_circle</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-16">
        {/* Sidebar reused from scan theme */}
        <OpsSidebar active="dashboard" className="hidden md:flex h-[calc(100vh-64px)] w-64" />

        {/* Main dashboard content */}
        <section className="flex-1 relative overflow-y-auto grid-bg p-6">
          <div className="w-full max-w-5xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-['Space_Grotesk'] text-2xl md:text-3xl font-extrabold tracking-tighter text-on-surface uppercase">
                  Operations Dashboard
                </h1>
                <p className="font-mono text-primary/60 text-[10px] uppercase tracking-widest mt-1">
                  Recent scan activity and score evolution
                </p>
              </div>
              <Link
                href="/"
                className="text-[11px] bg-primary text-on-primary px-4 py-2 rounded-sm font-mono uppercase tracking-widest hover:brightness-110 transition-colors"
              >
                + New Scan
              </Link>
            </div>

            {scoreHistory.length > 0 && (
              <div className="bg-surface-container-low border border-outline-variant/20 rounded-sm p-4">
                <ScoreHistory data={scoreHistory} />
              </div>
            )}

            <div className="text-xs font-mono text-on-surface/60 uppercase tracking-widest mb-2">
              Recent scans ({scans.length})
            </div>

            <div className="space-y-3">
              {scans.map(scan => (
                <Link
                  key={scan.scan_id}
                  href={scan.status === "complete" ? `/scan/${scan.scan_id}/report` : `/scan/${scan.scan_id}`}
                  className="block bg-surface-container-low border border-outline-variant/20 hover:border-outline-variant/40 rounded-sm p-5 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-sm bg-surface-container-high flex items-center justify-center border border-outline-variant/30">
                        <Shield className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-on-surface">
                          {scan.repo_name || scan.github_url || scan.scan_id.slice(0, 16)}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-on-surface/50">
                          <Clock className="w-3 h-3" />
                          <span>
                            {scan.created_at ? new Date(scan.created_at).toLocaleString() : "—"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {scan.score_before != null && scan.score_after != null && (
                        <div className="text-right">
                          <div className="text-[10px] text-on-surface/50 uppercase">Score</div>
                          <div className="text-sm font-mono">
                            <span className="text-secondary">{scan.score_before}</span>
                            <span className="text-on-surface/40 mx-1">→</span>
                            <span className="text-tertiary">{scan.score_after}</span>
                          </div>
                        </div>
                      )}
                      {scan.total_findings > 0 && (
                        <div className="text-right">
                          <div className="text-[10px] text-on-surface/50 uppercase">Findings</div>
                          <div className="text-sm font-mono text-on-surface">{scan.total_findings}</div>
                        </div>
                      )}
                      <span className={`text-[10px] px-2 py-1 rounded border uppercase font-mono tracking-widest ${
                        STATUS_STYLES[scan.status] || STATUS_STYLES.pending
                      }`}>
                        {scan.status}
                      </span>
                      <ExternalLink className="w-4 h-4 text-on-surface/40" />
                    </div>
                  </div>
                </Link>
              ))}

              {scans.length === 0 && (
                <div className="text-center py-16 text-on-surface/50">
                  <Shield className="w-8 h-8 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">No scans yet. Start your first scan.</p>
                  <Link href="/" className="text-primary text-sm mt-2 inline-block hover:underline">
                    Scan a repo →
                  </Link>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
