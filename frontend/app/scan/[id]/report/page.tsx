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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ReportPage() {
  const params = useParams()
  const scanId = params.id as string
  const [report, setReport] = useState<ScanReport | null>(null)
  const [activeTab, setActiveTab] = useState<"overview" | "findings" | "chains" | "patches" | "graph">("overview")
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
        <div className="text-on-surface-variant animate-pulse font-mono text-sm">Compiling blue team report...</div>
      </div>
    )
  }

  const TABS = [
    { key: "overview", label: "Overview" },
    { key: "findings", label: `Findings (${report.total_findings})` },
    { key: "chains", label: `Chains (${report.chains?.length || 0})` },
    { key: "patches", label: `Patches (${report.patches?.length || 0})` },
    { key: "graph", label: "Attack Graph" },
  ] as const

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Top bar */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-red-400" />
          <span className="font-semibold">CodeSentinel</span>
          <span className="text-gray-600">/</span>
          <span className="text-gray-400 text-sm">{report.repo_name || report.github_url}</span>
        </div>
        <div className="flex items-center gap-3">
          {/* Navigation */}
          <a href="/" className="text-sm text-gray-500 hover:text-gray-300 px-3 py-1.5 border border-gray-700 rounded-lg">
            return (
              <main className="bg-surface text-on-background font-body selection:bg-primary-container selection:text-on-primary-container overflow-hidden h-screen flex flex-col">
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
                  <aside className="bg-surface-container-low text-primary font-body text-xs uppercase tracking-widest font-semibold flex flex-col h-full border-r border-outline/15 w-64 fixed left-0 shadow-[4px_0_24px_rgba(152,203,255,0.05)] hidden md:flex">
                    <div className="p-6 mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-sm bg-surface-container-highest flex items-center justify-center border border-primary/20">
                          <Shield className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <p className="text-[10px] text-on-surface opacity-60 normal-case tracking-normal">CodeSentinel Ops</p>
                          <p className="text-primary font-bold tracking-tight text-xs">Level 4 Clearance</p>
                        </div>
                      </div>
                    </div>
                    <nav className="flex-1 px-4 space-y-1">
                      <div className="flex items-center gap-3 px-4 py-3 text-on-surface/60 hover:bg-surface-container hover:text-on-surface transition-all rounded-sm">
                        <span className="material-symbols-outlined">dashboard</span>
                        <span>Dashboard</span>
                      </div>
                      <div className="flex items-center gap-3 px-4 py-3 text-on-surface/60 hover:bg-surface-container hover:text-on-surface transition-all rounded-sm">
                        <span className="material-symbols-outlined">radar</span>
                        <span>Active Scans</span>
                      </div>
                      <div className="flex items-center gap-3 px-4 py-3 text-on-surface/60 hover:bg-surface-container hover:text-on-surface transition-all rounded-sm">
                        <span className="material-symbols-outlined">security</span>
                        <span>Red Team Reports</span>
                      </div>
                      <div className="bg-surface-container-high text-primary border-l-4 border-primary flex items-center gap-3 px-4 py-3 rounded-sm">
                        <span className="material-symbols-outlined">shield</span>
                        <span>Blue Team Reports</span>
                      </div>
                      <div className="flex items-center gap-3 px-4 py-3 text-on-surface/60 hover:bg-surface-container hover:text-on-surface transition-all rounded-sm">
                        <span className="material-symbols-outlined">settings</span>
                        <span>Settings</span>
                      </div>
                    </nav>
                    <div className="mt-auto p-4 space-y-1 border-top border-outline/10">
                      <div className="flex items-center gap-3 px-4 py-2 text-on-surface/60 hover:text-on-surface transition-all">
                        <span className="material-symbols-outlined text-sm">help_center</span>
                        <span className="text-[10px]">Support</span>
                      </div>
                      <div className="flex items-center gap-3 px-4 py-2 text-on-surface/60 hover:text-on-surface transition-all">
                        <span className="material-symbols-outlined text-sm">terminal</span>
                        <span className="text-[10px]">Logs</span>
                      </div>
                    </div>
                  </aside>

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
                                No known APT or threat actor fingerprint matched this scan. Findings are likely opportunistic rather than
                                targeted.
                              </p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Tabs + PR button row */}
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
                                  <div
                                    className={`text-xs mt-0.5 ${
                                      gc.still_present ? "text-secondary" : "text-primary"
                                    }`}
                                  >
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

                      {/* Graph */}
                      {activeTab === "graph" && report.attack_graph && <AttackGraph data={report.attack_graph} />}

                      {/* Footer telemetry */}
                      <div className="grid grid-cols-12 gap-6 mt-12 pb-12">
                        <div className="col-span-12 md:col-span-8 bg-surface-container-lowest p-6 rounded-sm border border-outline-variant/10 font-mono text-[11px] leading-relaxed text-on-surface/60 overflow-hidden">
                          <div className="flex items-center gap-2 text-tertiary mb-3 uppercase tracking-widest font-bold">
                            <span className="material-symbols-outlined text-sm">terminal</span>
                            Live System Log Trace
                          </div>
                          <p className="mb-1">
                            <span className="text-on-surface/20">[14:22:01]</span> <span className="text-primary">INFO:</span> Scanning
                            node cluster US-EAST-01...
                          </p>
                          <p className="mb-1">
                            <span className="text-on-surface/20">[14:22:05]</span> <span className="text-secondary">WARN:</span> Found
                            suspicious outbound packet.
                          </p>
                          <p className="mb-1">
                            <span className="text-on-surface/20">[14:22:08]</span> <span className="text-tertiary">SUCCESS:</span> IPS
                            blocked malicious string match in request body.
                          </p>
                          <p className="mb-1">
                            <span className="text-on-surface/20">[14:22:15]</span> <span className="text-primary">INFO:</span> Blue Team
                            automated report compiling...
                          </p>
                          <div className="w-2 h-4 bg-primary inline-block animate-pulse ml-1 align-middle" />
                        </div>
                        <div className="col-span-12 md:col-span-4 flex flex-col justify-between p-6 bg-gradient-to-br from-primary/10 to-transparent rounded-sm border border-primary/20">
                          <div>
                            <h5 className="font-headline font-bold text-on-surface uppercase tracking-tighter">Defense Readiness</h5>
                            <p className="text-xs text-on-surface/60 mt-1">
                              Based on current security findings and patch latency.
                            </p>
                          </div>
                          <div className="mt-8">
                            <div className="flex justify-between text-[10px] font-mono mb-2">
                              <span>SYSTEM UPTIME</span>
                              <span className="text-tertiary">99.98%</span>
                            </div>
                            <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden">
                              <div className="bg-tertiary h-full w-[99%]" />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              </main>
            )