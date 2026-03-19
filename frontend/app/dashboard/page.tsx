"use client"
import { useEffect, useState } from "react"
import Link from "next/link"
import { listScans } from "@/lib/api"
import { Shield, ExternalLink, Clock } from "lucide-react"
import ScoreHistory from "@/components/ScoreHistory"

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
    <main className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-red-400" />
          <span className="font-semibold">CodeSentinel</span>
          <span className="text-gray-600">/</span>
          <span className="text-gray-400 text-sm">Dashboard</span>
        </div>
        <Link href="/" className="text-sm bg-red-700 hover:bg-red-600 px-4 py-2 rounded-lg transition-colors">
          New Scan
        </Link>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {scoreHistory.length > 0 && (
          <div className="mb-8">
            <ScoreHistory data={scoreHistory} />
          </div>
        )}

        <div className="text-sm font-medium text-gray-400 mb-4">Recent scans ({scans.length})</div>

        <div className="space-y-3">
          {scans.map(scan => (
            <Link
              key={scan.scan_id}
              href={scan.status === "complete" ? `/scan/${scan.scan_id}/report` : `/scan/${scan.scan_id}`}
              className="block bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl p-5 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div>
                    <div className="text-sm font-medium text-white">
                      {scan.repo_name || scan.github_url || scan.scan_id.slice(0, 16)}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <Clock className="w-3 h-3 text-gray-600" />
                      <span className="text-xs text-gray-500">
                        {scan.created_at ? new Date(scan.created_at).toLocaleString() : "—"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {scan.score_before != null && scan.score_after != null && (
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Score</div>
                      <div className="text-sm font-mono">
                        <span className="text-red-400">{scan.score_before}</span>
                        <span className="text-gray-600 mx-1">→</span>
                        <span className="text-green-400">{scan.score_after}</span>
                      </div>
                    </div>
                  )}
                  {scan.total_findings > 0 && (
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Findings</div>
                      <div className="text-sm font-mono text-white">{scan.total_findings}</div>
                    </div>
                  )}
                  <span className={`text-xs px-2 py-1 rounded border ${STATUS_STYLES[scan.status] || STATUS_STYLES.pending}`}>
                    {scan.status}
                  </span>
                  <ExternalLink className="w-4 h-4 text-gray-600" />
                </div>
              </div>
            </Link>
          ))}

          {scans.length === 0 && (
            <div className="text-center py-16 text-gray-600">
              <Shield className="w-8 h-8 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No scans yet. Start your first scan.</p>
              <Link href="/" className="text-red-400 text-sm mt-2 inline-block hover:underline">
                Scan a repo →
              </Link>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
