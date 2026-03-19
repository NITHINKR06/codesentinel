"use client"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { getReport, createPR } from "@/lib/api"
import { ScanReport } from "@/types"
import ScoreGauge from "@/components/ScoreGauge"
import FindingCard from "@/components/FindingCard"
import AttackGraph from "@/components/AttackGraph"
import ThreatActorCard from "@/components/ThreatActorCard"
import PatchViewer from "@/components/PatchViewer"
import Link from "next/link"
import { Shield, GitPullRequest, AlertTriangle, Bug, History, Plus, LayoutDashboard } from "lucide-react"

export default function ReportPage() {
  const params = useParams()
  const scanId = params.id as string
  const [report, setReport] = useState<ScanReport | null>(null)
  const [activeTab, setActiveTab] = useState<"overview" | "findings" | "chains" | "patches" | "graph">("overview")
  const [prToken, setPrToken] = useState("")
  const [prLoading, setPrLoading] = useState(false)
  const [prUrl, setPrUrl] = useState("")

  useEffect(() => {
    getReport(scanId).then(setReport)
  }, [scanId])

  async function handleCreatePR() {
    if (!report?.github_url || !prToken) return
    setPrLoading(true)
    try {
      const res = await createPR(scanId, prToken, report.github_url)
      setPrUrl(res.pr_url)
    } finally {
      setPrLoading(false)
    }
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400 animate-pulse">Loading report...</div>
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
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-red-400" />
            <Link href="/" className="font-semibold hover:text-red-400 transition-colors">CodeSentinel</Link>
            <span className="text-gray-600">/</span>
            <span className="text-gray-400 text-sm">{report.repo_name || report.github_url}</span>
          </div>
          
          <div className="w-px h-6 bg-gray-800 mx-2"></div>
          
          <nav className="flex items-center gap-4 text-sm text-gray-400">
            <Link href="/" className="flex items-center gap-1.5 hover:text-white transition-colors border border-transparent hover:border-gray-800 px-2.5 py-1.5 rounded-lg">
              <Plus className="w-4 h-4" /> New Scan
            </Link>
            <Link href="/dashboard" className="flex items-center gap-1.5 hover:text-white transition-colors border border-transparent hover:border-gray-800 px-2.5 py-1.5 rounded-lg">
              <LayoutDashboard className="w-4 h-4" /> Dashboard
            </Link>
          </nav>
        </div>
        
        <div className="flex items-center gap-3">
          {report.pr_url || prUrl ? (
          <a href={report.pr_url || prUrl} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-green-400 border border-green-800 px-3 py-1.5 rounded-lg hover:bg-green-900/20">
            <GitPullRequest className="w-4 h-4" /> View PR
          </a>
        ) : report.github_url ? (
          <div className="flex items-center gap-2">
            <input
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 w-48"
              placeholder="GitHub token"
              type="password"
              value={prToken}
              onChange={e => setPrToken(e.target.value)}
            />
            <button onClick={handleCreatePR} disabled={prLoading || !prToken}
              className="flex items-center gap-2 text-sm bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 px-3 py-1.5 rounded-lg">
              <GitPullRequest className="w-4 h-4" />
              {prLoading ? "Creating..." : "Open PR"}
            </button>
          </div>
        ) : null}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Score row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 flex items-center gap-6">
            <ScoreGauge score={report.score_before || 0} label="Before" />
            <div className="text-gray-600 text-2xl">→</div>
            <ScoreGauge score={report.score_after || 0} label="After" />
          </div>
          <div className="bg-gray-900 border border-red-900/40 rounded-xl p-4 flex flex-col justify-center">
            <div className="text-3xl font-bold text-red-400">{report.critical_count}</div>
            <div className="text-xs text-gray-500 mt-1">Critical findings</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col justify-center">
            <div className="text-3xl font-bold text-orange-400">{report.chains?.length || 0}</div>
            <div className="text-xs text-gray-500 mt-1">Exploit chains</div>
          </div>
        </div>

        {/* Threat actor */}
        {report.threat_actor && <ThreatActorCard actor={report.threat_actor} />}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-gray-800 pb-0">
          {TABS.map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm rounded-t-lg border-b-2 -mb-px transition-colors ${
                activeTab === tab.key
                  ? "border-red-500 text-white"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview */}
        {activeTab === "overview" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-gray-300">
                  <Bug className="w-4 h-4 text-red-400" /> Top critical findings
                </div>
                {report.findings.filter(f => f.severity === "critical").slice(0, 5).map(f => (
                  <div key={f.id} className="py-2 border-b border-gray-800 last:border-0">
                    <div className="text-sm text-white">{f.title}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{f.file_path}:{f.line_number}</div>
                    <div className="text-xs text-red-400 mt-0.5">{f.plain_impact}</div>
                  </div>
                ))}
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-gray-300">
                  <History className="w-4 h-4 text-orange-400" /> Git history leaks
                </div>
                {(report.ghost_commits || []).slice(0, 5).map((gc, i) => (
                  <div key={i} className="py-2 border-b border-gray-800 last:border-0">
                    <div className="text-sm text-white">{gc.secret_type}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{gc.file} — {gc.commit_sha}</div>
                    <div className={`text-xs mt-0.5 ${gc.still_present ? "text-red-400" : "text-yellow-500"}`}>
                      {gc.still_present ? "⚠ Still present in code" : "Deleted (still in history)"}
                    </div>
                  </div>
                ))}
                {(!report.ghost_commits || report.ghost_commits.length === 0) && (
                  <div className="text-sm text-green-400">No secrets found in git history ✓</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Findings */}
        {activeTab === "findings" && (
          <div className="space-y-3">
            {report.findings.map(f => <FindingCard key={f.id} finding={f} />)}
          </div>
        )}

        {/* Chains */}
        {activeTab === "chains" && (
          <div className="space-y-4">
            {report.chains?.map(chain => (
              <div key={chain.chain_id} className="bg-gray-900 border border-red-900/50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <span className="font-medium text-red-400 text-sm">
                    {chain.escalated_severity.toUpperCase()} — {chain.length}-step exploit chain
                  </span>
                </div>
                <pre className="text-xs text-gray-300 whitespace-pre-wrap bg-gray-800 rounded-lg p-3">
                  {chain.attack_narrative}
                </pre>
              </div>
            ))}
            {(!report.chains || report.chains.length === 0) && (
              <div className="text-gray-500 text-sm">No exploit chains found.</div>
            )}
          </div>
        )}

        {/* Patches */}
        {activeTab === "patches" && (
          <div className="space-y-4">
            {report.patches?.map((patch, i) => <PatchViewer key={i} patch={patch} />)}
          </div>
        )}

        {/* Graph */}
        {activeTab === "graph" && report.attack_graph && (
          <AttackGraph data={report.attack_graph} />
        )}
      </div>
    </main>
  )
}
