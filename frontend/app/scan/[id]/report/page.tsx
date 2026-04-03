"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { getReport } from "@/lib/api"
import { ScanReport } from "@/types"
import ScoreGauge from "@/components/ScoreGauge"
import FindingCard from "@/components/FindingCard"
import AttackGraph from "@/components/AttackGraph"
import ThreatActorCard from "@/components/ThreatActorCard"
import PatchViewer from "@/components/PatchViewer"
import { Shield, GitPullRequest, AlertTriangle, Bug, History } from "lucide-react"
import OpsSidebar from "@/components/OpsSidebar"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ReportPage() {
  const params = useParams()
  const scanId = params.id as string
  const [report, setReport] = useState<ScanReport | null>(null)
  const [activeTab, setActiveTab] = useState<"overview" | "findings" | "chains" | "patches" | "simulations" | "graph">("overview")
  const [prLoading, setPrLoading] = useState(false)
  const [prUrl, setPrUrl] = useState("")
  const [prError, setPrError] = useState("")

  useEffect(() => {
    getReport(scanId).then(setReport)
  }, [scanId])

  async function handleCreatePR() {
    if (!report?.github_url) return
    setPrLoading(true)
    setPrError("")
    try {
      const res = await fetch(`${API_URL}/api/github/pr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scan_id: scanId,
          repo_url: report.github_url,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "PR creation failed")
      }
      const data = await res.json()
      setPrUrl(data.pr_url)
    } catch (e: unknown) {
      setPrError(e instanceof Error ? e.message : "Failed to create PR")
    } finally {
      setPrLoading(false)
    }
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center text-on-surface">
        <div className="text-on-surface-variant animate-pulse font-mono text-sm">
          Compiling blue team report...
        </div>
      </div>
    )
  }

  const simulations = report.attack_graph?.simulations || []
  const confirmedCount = simulations.filter((s) => s.confirmed).length

  const TABS = [
    { key: "overview", label: "Overview" },
    { key: "findings", label: `Findings (${report.total_findings})` },
    { key: "chains", label: `Chains (${report.chains?.length || 0})` },
    { key: "patches", label: `Patches (${report.patches?.length || 0})` },
    { key: "simulations", label: `Simulations (${confirmedCount}/${simulations.length})` },
    { key: "graph", label: "Attack Graph" },
  ] as const

  return (
    <main className="bg-surface text-on-background font-body selection:bg-primary-container selection:text-on-primary-container overflow-hidden min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="bg-[#131313] text-primary font-headline text-sm tracking-tight flex justify-between items-center w-full px-6 py-3 h-16 z-50 fixed top-0 border-b border-outline/15">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-primary">CodeSentinel</span>
          <div className="hidden md:flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-sm border border-outline/20">
            <span className="material-symbols-outlined text-xs">search</span>
            <input
              className="bg-transparent border-none focus:ring-0 text-xs w-64 placeholder:opacity-40 text-on-surface"
              placeholder="Global Scan Search..."
              type="text"
            />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="/"
            className="hidden md:inline-flex text-[11px] text-on-surface/70 border border-outline/40 px-3 py-1.5 rounded-sm hover:bg-surface-container-high hover:text-primary transition-colors"
          >
            + New Scan
          </a>
          <a
            href="/dashboard"
            className="hidden md:inline-flex text-[11px] text-on-surface/70 border border-outline/40 px-3 py-1.5 rounded-sm hover:bg-surface-container-high hover:text-primary transition-colors"
          >
            Dashboard
          </a>
          {report.pr_url || prUrl ? (
            <a
              href={report.pr_url || prUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-[11px] bg-tertiary/20 text-tertiary border border-tertiary/50 px-4 py-2 rounded-sm hover:bg-tertiary/30 font-mono uppercase tracking-widest"
            >
              <GitPullRequest className="w-4 h-4" /> View PR
            </a>
          ) : report.github_url ? (
            <button
              onClick={handleCreatePR}
              disabled={prLoading}
              className="inline-flex items-center gap-2 text-[11px] bg-primary text-on-primary border border-primary/60 px-4 py-2 rounded-sm hover:brightness-110 disabled:opacity-50 font-mono uppercase tracking-widest"
              type="button"
            >
              <GitPullRequest className="w-4 h-4" />
              {prLoading ? "Creating PR..." : "Generate PR"}
            </button>
          ) : null}
        </div>
      </header>

      <div className="flex flex-1 pt-16 overflow-hidden">
        {/* Side navigation */}
        <OpsSidebar
          active="blue"
          scanId={scanId}
          className="hidden md:flex bg-surface-container-low text-primary font-body text-xs uppercase tracking-widest font-semibold h-full border-r border-outline/15 w-64 fixed left-0 shadow-[4px_0_24px_rgba(152,203,255,0.05)]"
        />

        {/* Main report content */}
        <section className="md:ml-64 flex-1 overflow-y-auto bg-surface p-8 scroll-smooth">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Score + threat header */}
            <div className="grid grid-cols-12 gap-6">
              {/* Gauge */}
              <div className="col-span-12 lg:col-span-3 bg-surface-container-low p-6 rounded-sm flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-secondary-container/30" />
                <div className="relative w-32 h-32 rounded-full flex items-center justify-center">
                  <ScoreGauge score={report.score_after || 0} label="Score" />
                </div>
                <p className="mt-4 font-headline text-xs font-bold text-secondary-container tracking-widest uppercase">
                  Critical Vulnerability
                </p>
              </div>

              {/* KPIs */}
              <div className="col-span-12 lg:col-span-5 grid grid-cols-2 gap-4">
                <div className="bg-surface-container p-6 rounded-sm border-l-4 border-secondary-container">
                  <p className="text-xs text-on-surface/60">Critical Findings</p>
                  <p className="text-4xl font-headline font-bold text-on-surface mt-2">{report.critical_count}</p>
                  <div className="mt-4 flex items-center gap-2 text-[10px] text-secondary">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Across {report.total_findings} total findings</span>
                  </div>
                </div>
                <div className="bg-surface-container p-6 rounded-sm border-l-4 border-primary">
                  <p className="text-xs text-on-surface/60">Exploit Chains</p>
                  <div className="flex items-baseline gap-2 mt-2">
                    <p className="text-4xl font-headline font-bold text-on-surface">{report.chains?.length || 0}</p>
                  </div>
                  <div className="mt-4 w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div className="bg-primary h-full" style={{ width: `${Math.min(100, (report.chains?.length || 0) * 20)}%` }} />
                  </div>
                </div>
              </div>

              {/* Threat actor */}
              <div className="col-span-12 lg:col-span-4 bg-surface-container-low p-6 rounded-sm relative border border-outline-variant/10">
                {report.threat_actor ? (
                  <ThreatActorCard actor={report.threat_actor} />
                ) : (
                  <div className="flex flex-col justify-between h-full">
                    <div>
                      <p className="text-[10px] text-primary font-mono uppercase tracking-[0.2em]">Threat Actor Profile</p>
                      <h3 className="text-xl font-headline font-bold text-on-surface mt-1 uppercase">No Pattern Matched</h3>
                    </div>
                    <p className="mt-4 text-xs text-on-surface/60">
                      No known APT or threat actor fingerprint matched this scan. Findings are likely opportunistic rather than targeted.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Tabs row */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-6 border-b border-outline-variant/20 pb-0">
              <div className="flex gap-8 overflow-x-auto w-full md:w-auto">
                {TABS.map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`pb-4 text-xs font-headline font-bold uppercase tracking-widest whitespace-nowrap border-b-2 ${
                      activeTab === tab.key
                        ? "text-primary border-primary"
                        : "text-on-surface/40 border-transparent hover:text-on-surface"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {prError && (
              <div className="bg-error-container/20 border border-error-container text-on-error-container text-xs font-mono px-4 py-2 rounded-sm">
                {prError} — Check GITHUB_TOKEN configuration.
              </div>
            )}

            {/* Overview */}
            {activeTab === "overview" && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-surface-container-low p-5 rounded-sm border border-outline-variant/20">
                    <div className="flex items-center gap-2 mb-3 text-sm font-medium text-on-surface">
                      <Bug className="w-4 h-4 text-secondary" /> Top critical findings
                    </div>
                    {report.findings
                      .filter((f: any) => f.severity === "critical")
                      .slice(0, 5)
                      .map((f: any) => (
                        <div key={f.id} className="py-2 border-b border-outline-variant/20 last:border-0">
                          <div className="text-sm text-on-surface font-headline">{f.title}</div>
                          <div className="text-xs text-on-surface/60 mt-0.5 font-mono">
                            {f.file_path}:{f.line_number}
                          </div>
                          <div className="text-xs text-secondary mt-0.5">{f.plain_impact}</div>
                        </div>
                      ))}
                    {report.findings.filter((f: any) => f.severity === "critical").length === 0 && (
                      <div className="text-sm text-tertiary">No critical findings ✓</div>
                    )}
                  </div>
                  <div className="bg-surface-container-low p-5 rounded-sm border border-outline-variant/20">
                    <div className="flex items-center gap-2 mb-3 text-sm font-medium text-on-surface">
                      <History className="w-4 h-4 text-primary" /> Git history leaks
                    </div>
                    {(report.ghost_commits || []).slice(0, 5).map((gc: any, i: number) => (
                      <div key={i} className="py-2 border-b border-outline-variant/20 last:border-0">
                        <div className="text-sm text-on-surface font-headline">{gc.secret_type}</div>
                        <div className="text-xs text-on-surface/60 mt-0.5 font-mono">
                          {gc.file} — {gc.commit_sha}
                        </div>
                        <div className={`text-xs mt-0.5 ${gc.still_present ? "text-secondary" : "text-primary"}`}>
                          {gc.still_present ? "Still present in code" : "Deleted (remains in history)"}
                        </div>
                      </div>
                    ))}
                    {(!report.ghost_commits || report.ghost_commits.length === 0) && (
                      <div className="text-sm text-tertiary">No secrets found in git history ✓</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Findings */}
            {activeTab === "findings" && (
              <div className="space-y-3">
                {report.findings.map((f: any) => (
                  <FindingCard key={f.id} finding={f} />
                ))}
              </div>
            )}

            {/* Chains */}
            {activeTab === "chains" && (
              <div className="space-y-4">
                {report.chains?.map((chain: any) => (
                  <div key={chain.chain_id} className="bg-surface-container-low p-5 rounded-sm border border-secondary/40">
                    <div className="flex items-center gap-3 mb-3">
                      <AlertTriangle className="w-5 h-5 text-secondary" />
                      <span className="font-medium text-secondary text-sm">
                        {chain.escalated_severity?.toUpperCase()} — {chain.length}-step exploit chain
                      </span>
                    </div>
                    <pre className="text-xs text-on-surface-variant whitespace-pre-wrap bg-surface-container-high rounded p-3">
                      {chain.attack_narrative}
                    </pre>
                  </div>
                ))}
                {(!report.chains || report.chains.length === 0) && (
                  <div className="text-on-surface-variant text-sm">
                    No exploit chains found — vulnerabilities are isolated with no connected attack paths.
                  </div>
                )}
              </div>
            )}

            {/* Patches */}
            {activeTab === "patches" && (
              <div className="space-y-4">
                {report.patches?.map((patch: any, i: number) => (
                  <PatchViewer key={i} patch={patch} />
                ))}
              </div>
            )}

            {/* Simulations */}
            {activeTab === "simulations" && (
              <div className="space-y-4">
                {simulations.map((sim, i) => (
                  <div
                    key={`${sim.vuln_type}_${sim.file_path}_${i}`}
                    className="bg-surface-container-low p-5 rounded-sm border border-outline-variant/20"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <div className="text-sm font-headline font-bold text-on-surface uppercase tracking-widest">
                          {sim.vuln_type}
                        </div>
                        <div className="text-xs text-on-surface/60 font-mono break-all mt-1">
                          {sim.file_path}
                        </div>
                      </div>
                      <div
                        className={
                          "shrink-0 text-[10px] font-mono uppercase tracking-widest px-3 py-1 rounded-sm border " +
                          (sim.confirmed
                            ? "bg-tertiary/15 text-tertiary border-tertiary/40"
                            : "bg-surface-container-high text-on-surface/60 border-outline/20")
                        }
                      >
                        {sim.confirmed ? "CONFIRMED" : "INCONCLUSIVE"}
                      </div>
                    </div>

                    {sim.target_url && (
                      <div className="text-[10px] text-on-surface/60 font-mono mt-3">
                        Target: <span className="text-on-surface">{sim.target_url}</span>
                      </div>
                    )}

                    {/* Payload + HTTP details */}
                    {sim.observations && sim.observations.length > 0 && (
                      <div className="mt-4 space-y-3">
                        {sim.observations.map((obs, oi) => {
                          const req = (obs.request || {}) as any
                          const res = (obs.result || {}) as any
                          const url = typeof res.url === "string" ? res.url : ""
                          const status = typeof res.status_code === "number" ? res.status_code : undefined
                          const body = typeof res.body === "string" ? res.body : ""
                          const method = typeof req.method === "string" ? req.method : ""
                          const path = typeof req.path === "string" ? req.path : ""
                          const paramName = typeof req.param_name === "string" ? req.param_name : ""
                          const payload = typeof req.payload === "string" ? req.payload : ""
                          const command = typeof req.command === "string" ? req.command : ""

                          return (
                            <div key={`${obs.step}_${oi}`} className="bg-surface-container-high rounded p-3 border border-outline-variant/10">
                              <div className="flex items-center justify-between gap-3">
                                <div className="text-[10px] font-mono text-on-surface/70 uppercase tracking-widest">
                                  Step {obs.step}: {obs.action}
                                  {obs.payload_name ? ` — ${obs.payload_name}` : ""}
                                </div>
                                {typeof status === "number" && (
                                  <div className="text-[10px] font-mono text-on-surface/60">
                                    HTTP {status}
                                  </div>
                                )}
                              </div>

                              {url && (
                                <div className="mt-2 text-[10px] font-mono text-on-surface/60 break-all">
                                  {method ? `${method} ` : ""}{url}{path && !url.endsWith(path) ? ` (${path})` : ""}
                                </div>
                              )}

                              {command && (
                                <div className="mt-2 text-[10px] font-mono text-on-surface/60 break-all">
                                  Command: <span className="text-on-surface">{command}</span>
                                </div>
                              )}

                              {(payload || paramName) && (
                                <div className="mt-2 text-[10px] font-mono text-on-surface/60 break-all">
                                  Payload{paramName ? ` (${paramName})` : ""}: <span className="text-on-surface">{payload || "(empty)"}</span>
                                </div>
                              )}

                              {body && (
                                <div className="mt-2 text-xs text-on-surface-variant whitespace-pre-wrap">
                                  {body.slice(0, 500)}{body.length > 500 ? "…" : ""}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}

                    <div className="mt-3 text-xs text-on-surface-variant whitespace-pre-wrap bg-surface-container-high rounded p-3 border border-outline-variant/10">
                      {sim.confirmation_message || sim.evidence || "No evidence captured."}
                    </div>

                    {sim.simulation_notes && (
                      <div className="mt-2 text-[10px] text-on-surface/50 font-mono">
                        {sim.simulation_notes}
                      </div>
                    )}
                  </div>
                ))}

                {simulations.length === 0 && (
                  <div className="text-on-surface-variant text-sm">
                    No simulations were run for this scan. The sandbox only simulates a subset of vuln types
                    (e.g. SQLi/XSS/SSRF/RCE/path traversal) and only for high/critical findings.
                  </div>
                )}
              </div>
            )}

            {/* Graph */}
            {activeTab === "graph" && report.attack_graph && <AttackGraph data={report.attack_graph} />}
          </div>
        </section>
      </div>
    </main>
  )
}
