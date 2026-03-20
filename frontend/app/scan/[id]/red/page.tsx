"use client"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { getReport } from "@/lib/api"
import { ScanReport } from "@/types"
import {
  Shield, Terminal, AlertTriangle, Globe, GitCommit,
  Cpu, ChevronDown, ChevronUp, Target, Zap, Eye
} from "lucide-react"

const SEV_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-900/20 border-red-800",
  high: "text-orange-400 bg-orange-900/20 border-orange-800",
  medium: "text-yellow-400 bg-yellow-900/20 border-yellow-800",
  low: "text-blue-400 bg-blue-900/20 border-blue-800",
  CRITICAL: "text-red-400 bg-red-900/20 border-red-800",
  HIGH: "text-orange-400 bg-orange-900/20 border-orange-800",
}

export default function RedTeamPage() {
  const params = useParams()
  const scanId = params.id as string
  const [report, setReport] = useState<ScanReport | null>(null)
  const [activeSection, setActiveSection] = useState<string>("narrative")

  useEffect(() => {
    getReport(scanId).then(setReport)
  }, [scanId])

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-red-400 animate-pulse font-mono text-sm">
          [red agent] loading intelligence...
        </div>
      </div>
    )
  }

  const attackGraph = report.attack_graph as any
  const recon = attackGraph?.recon || {}
  const simulations = attackGraph?.simulations || []
  const confirmedSims = simulations.filter((s: any) => s.confirmed)

  const sections = [
    { key: "narrative", label: "Attack Narrative", icon: Terminal },
    { key: "recon", label: "Recon Intel", icon: Eye },
    { key: "simulation", label: `Simulations (${confirmedSims.length} confirmed)`, icon: Zap },
    { key: "chains", label: `Chains (${report.chains?.length || 0})`, icon: Target },
    { key: "ghost", label: `Git Secrets (${report.ghost_commits?.length || 0})`, icon: GitCommit },
  ]

  return (
    <main className="min-h-screen bg-gray-950 text-white font-mono">
      {/* Header */}
      <header className="border-b border-red-900/50 px-6 py-4 bg-red-950/10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-red-400" />
            <span className="text-red-400 font-semibold">RED TEAM</span>
            <span className="text-gray-600">/</span>
            <span className="text-gray-400 text-sm">{report.repo_name || report.github_url}</span>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="text-red-400">{report.critical_count} critical</span>
            <span className="text-orange-400">{report.high_count} high</span>
            <span className="text-gray-500">score: {report.score_before}/100</span>
            <a
              href={`/scan/${scanId}/report`}
              className="text-blue-400 border border-blue-800 px-3 py-1 rounded hover:bg-blue-900/20"
            >
              → Blue Team
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: "Exploit surface", value: report.total_findings, color: "text-red-400" },
            { label: "Confirmed exploits", value: confirmedSims.length, color: "text-orange-400" },
            { label: "Attack chains", value: report.chains?.length || 0, color: "text-yellow-400" },
            { label: "Git secrets", value: report.ghost_commits?.length || 0, color: "text-purple-400" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className={`text-3xl font-bold ${color}`}>{value}</div>
              <div className="text-xs text-gray-500 mt-1 font-sans">{label}</div>
            </div>
          ))}
        </div>

        {/* Threat actor banner */}
        {report.threat_actor && (
          <div className="bg-red-950/30 border border-red-900/50 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
              <div className="flex-1">
                <span className="text-red-400 font-semibold">{report.threat_actor.name}</span>
                <span className="text-gray-400 text-sm ml-3 font-sans">
                  {report.threat_actor.match_explanation}
                </span>
              </div>
              <span className="text-xs text-red-300 bg-red-900/40 border border-red-800 px-2 py-1 rounded">
                match: {report.threat_actor.match_score}
              </span>
            </div>
          </div>
        )}

        {/* Section tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {sections.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm border transition-all ${
                activeSection === key
                  ? "bg-red-900/30 border-red-700 text-red-300"
                  : "border-gray-800 text-gray-500 hover:border-gray-600 hover:text-gray-300"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* NARRATIVE */}
        {activeSection === "narrative" && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4 text-sm text-red-400">
              <Terminal className="w-4 h-4" />
              AI-Generated Attack Narrative
            </div>
            {attackGraph?.narrative ? (
              <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed font-mono">
                {attackGraph.narrative}
              </pre>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-400 font-sans">
                  No narrative generated yet — run a new scan to generate the AI attack story.
                </p>
                {/* Auto-generate from findings */}
                <div className="bg-gray-800 rounded-lg p-4 text-xs text-gray-300 font-mono">
                  <div className="text-red-400 mb-2"># Auto-generated attack path</div>
                  {report.findings?.filter((f: any) => f.severity === "critical").slice(0, 3).map((f: any, i: number) => (
                    <div key={i} className="mb-2">
                      <span className="text-orange-400">Step {i+1}:</span> Exploit {f.title} in{" "}
                      <span className="text-yellow-400">{f.file_path}:{f.line_number}</span>
                      <br />
                      <span className="text-gray-500 pl-4">→ {f.plain_impact}</span>
                    </div>
                  ))}
                  {(!report.findings || report.findings.filter((f: any) => f.severity === "critical").length === 0) && (
                    <div className="text-green-400">No critical findings — attack surface is limited</div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* RECON */}
        {activeSection === "recon" && (
          <div className="space-y-4">
            {/* Tech stack */}
            {recon.tech_stack?.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm text-gray-300">
                  <Cpu className="w-4 h-4 text-blue-400" />
                  <span className="font-sans">Tech Stack Fingerprint</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {recon.tech_stack.map((t: any, i: number) => (
                    <span key={i} className="text-xs px-3 py-1 bg-blue-900/20 border border-blue-800 text-blue-300 rounded font-mono">
                      {t.tech}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Exposed secrets */}
            {recon.exposed_secrets?.length > 0 && (
              <div className="bg-gray-900 border border-red-900/50 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm text-red-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="font-sans">Exposed Secrets ({recon.exposed_secrets.length})</span>
                </div>
                <div className="space-y-2">
                  {recon.exposed_secrets.map((s: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
                      <span className={`text-xs px-2 py-0.5 rounded border shrink-0 ${SEV_COLORS[s.severity] || ""}`}>
                        {s.severity}
                      </span>
                      <div>
                        <div className="text-sm text-white font-sans">{s.type}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{s.file}:{s.line}</div>
                        <div className="text-xs text-red-400 mt-0.5 font-sans">{s.attacker_value}</div>
                      </div>
                      <code className="text-xs text-orange-300 ml-auto shrink-0">{s.preview}</code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Attack surface */}
            {recon.attack_surface?.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm text-gray-300">
                  <Globe className="w-4 h-4 text-green-400" />
                  <span className="font-sans">Attack Surface — {recon.attack_surface.length} endpoints</span>
                </div>
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {recon.attack_surface.map((e: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 py-1.5 border-b border-gray-800/50 last:border-0">
                      <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                        e.method === "POST" || e.method === "DELETE" ? "text-red-300 bg-red-900/20" :
                        "text-green-300 bg-green-900/20"
                      }`}>
                        {e.method}
                      </span>
                      <code className="text-sm text-yellow-300 flex-1">{e.path}</code>
                      <span className="text-xs text-gray-600">{e.file}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Dependency vulns */}
            {recon.dependency_vulns?.length > 0 && (
              <div className="bg-gray-900 border border-orange-900/40 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3 text-sm text-orange-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="font-sans">Vulnerable Dependencies ({recon.dependency_vulns.length})</span>
                </div>
                <div className="space-y-2">
                  {recon.dependency_vulns.map((d: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-800 last:border-0">
                      <span className={`text-xs px-2 py-0.5 rounded border shrink-0 ${SEV_COLORS[d.severity] || ""}`}>
                        {d.severity}
                      </span>
                      <code className="text-sm text-white">{d.package}@{d.version}</code>
                      <span className="text-xs text-gray-400 font-sans flex-1">{d.description}</span>
                      <span className="text-xs text-gray-600">{d.vulnerable_range}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {Object.keys(recon).length === 0 && (
              <div className="text-gray-500 text-sm font-sans p-4">
                No recon data — run a new scan to populate intelligence.
              </div>
            )}
          </div>
        )}

        {/* SIMULATIONS */}
        {activeSection === "simulation" && (
          <div className="space-y-3">
            {simulations.length === 0 && (
              <div className="text-gray-500 text-sm font-sans p-4">
                No simulations run — scan needs PoC exploits generated first.
              </div>
            )}
            {simulations.map((sim: any, i: number) => (
              <div key={i} className={`border rounded-xl overflow-hidden ${
                sim.confirmed
                  ? "border-red-900/60 bg-red-950/10"
                  : "border-gray-800 bg-gray-900"
              }`}>
                <div className="flex items-center gap-3 px-5 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded border font-mono shrink-0 ${
                    sim.confirmed
                      ? "text-red-300 bg-red-900/30 border-red-700"
                      : "text-gray-400 bg-gray-800 border-gray-700"
                  }`}>
                    {sim.confirmed ? "CONFIRMED ✓" : "INCONCLUSIVE"}
                  </span>
                  <span className="text-sm text-white font-sans flex-1">{sim.vuln_type}</span>
                  <span className="text-xs text-gray-500">{sim.file_path}</span>
                  <span className="text-xs text-gray-600">{sim.duration_ms}ms</span>
                </div>
                {sim.confirmed && (
                  <div className="px-5 pb-4 border-t border-red-900/30">
                    <div className="text-xs text-red-300 mb-2 mt-3 font-sans">{sim.confirmation_message}</div>
                    {sim.output && (
                      <pre className="text-xs text-green-300 bg-gray-950 rounded-lg p-3 overflow-x-auto max-h-32">
                        {sim.output}
                      </pre>
                    )}
                    <div className="text-xs text-gray-600 mt-2">{sim.simulation_notes}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* CHAINS */}
        {activeSection === "chains" && (
          <div className="space-y-4">
            {(!report.chains || report.chains.length === 0) && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-sm text-gray-400 font-sans">
                No exploit chains detected. Chains require multiple vulnerabilities connected through function call paths.
                Try scanning a larger backend codebase with cross-file function calls.
              </div>
            )}
            {report.chains?.map((chain: any) => (
              <div key={chain.chain_id} className="bg-gray-900 border border-red-900/50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <Target className="w-4 h-4 text-red-400 shrink-0" />
                  <span className={`text-xs px-2 py-0.5 rounded border ${SEV_COLORS[chain.escalated_severity] || ""}`}>
                    {chain.escalated_severity?.toUpperCase()}
                  </span>
                  <span className="text-sm font-sans text-white">
                    {chain.length}-step exploit chain — {chain.vulns?.length} vulnerabilities
                  </span>
                </div>
                <pre className="text-xs text-gray-300 whitespace-pre-wrap bg-gray-950 rounded-lg p-3 leading-relaxed">
                  {chain.attack_narrative}
                </pre>
                <div className="mt-3 flex flex-wrap gap-2">
                  {chain.nodes?.map((node: string, i: number) => (
                    <span key={i} className="text-xs font-mono text-orange-300 bg-orange-900/20 px-2 py-0.5 rounded">
                      {node.split("::")[1] || node}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* GHOST COMMITS */}
        {activeSection === "ghost" && (
          <div className="space-y-3">
            {(!report.ghost_commits || report.ghost_commits.length === 0) && (
              <div className="text-green-400 text-sm font-sans p-4">
                ✓ No secrets found in git history
              </div>
            )}
            {report.ghost_commits?.map((gc: any, i: number) => (
              <div key={i} className={`border rounded-xl p-5 ${
                gc.still_present
                  ? "border-red-900/60 bg-red-950/10"
                  : "border-gray-800 bg-gray-900"
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  <GitCommit className="w-4 h-4 text-purple-400 shrink-0" />
                  <span className="text-sm text-white font-sans">{gc.secret_type}</span>
                  {gc.still_present && (
                    <span className="text-xs text-red-300 bg-red-900/30 border border-red-700 px-2 py-0.5 rounded">
                      STILL ACTIVE
                    </span>
                  )}
                  <span className="text-xs text-gray-500 ml-auto font-mono">{gc.commit_sha}</span>
                </div>
                <code className="text-xs text-orange-300">{gc.secret_preview}</code>
                <div className="text-xs text-gray-400 mt-2 font-sans">{gc.plain_impact}</div>
                <div className="text-xs text-gray-600 mt-1">{gc.file} — {gc.author}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
