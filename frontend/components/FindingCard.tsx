// FindingCard.tsx
"use client"
import { useState } from "react"
import { Finding } from "@/types"
import { ChevronDown, ChevronUp, Terminal } from "lucide-react"

const SEV_STYLES: Record<string, string> = {
  critical: "bg-red-900/30 border-red-800 text-red-400",
  high: "bg-orange-900/20 border-orange-800 text-orange-400",
  medium: "bg-yellow-900/20 border-yellow-800 text-yellow-400",
  low: "bg-blue-900/20 border-blue-800 text-blue-400",
}

export function FindingCard({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`border rounded-xl overflow-hidden ${SEV_STYLES[finding.severity]}`}>
      <button
        className="w-full flex items-center gap-3 px-5 py-4 text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-xs font-mono uppercase tracking-wider px-2 py-0.5 rounded border border-current">
          {finding.severity}
        </span>
        <span className="flex-1 text-white text-sm font-medium">{finding.title}</span>
        <span className="text-gray-500 text-xs font-mono">{finding.file_path}:{finding.line_number}</span>
        {expanded ? <ChevronUp className="w-4 h-4 shrink-0" /> : <ChevronDown className="w-4 h-4 shrink-0" />}
      </button>

      {expanded && (
        <div className="px-5 pb-5 border-t border-current/20 pt-4 space-y-4 bg-gray-950/50">
          <div>
            <div className="text-xs text-gray-500 mb-1">Impact</div>
            <p className="text-sm text-white">{finding.plain_impact}</p>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Details</div>
            <p className="text-sm text-gray-300">{finding.description}</p>
          </div>
          {finding.vulnerable_code && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Vulnerable code</div>
              <pre className="text-xs bg-gray-900 rounded-lg p-3 overflow-x-auto text-red-300 border border-red-900/30">
                {finding.vulnerable_code}
              </pre>
            </div>
          )}
          {finding.poc_exploit && (
            <div>
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                <Terminal className="w-3 h-3" /> PoC Exploit
              </div>
              <pre className="text-xs bg-gray-900 rounded-lg p-3 overflow-x-auto text-orange-300 border border-orange-900/30">
                {finding.poc_exploit}
              </pre>
            </div>
          )}
          {finding.mitre_technique && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="bg-gray-800 px-2 py-0.5 rounded font-mono">{finding.mitre_technique}</span>
              <span>{finding.mitre_tactic}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FindingCard
