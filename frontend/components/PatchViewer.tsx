"use client"
import { useState } from "react"
import { Patch } from "@/types"
import { CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react"

export default function PatchViewer({ patch }: { patch: Patch }) {
  const [expanded, setExpanded] = useState(false)

  const origLines = patch.original_code.split("\n")
  const patchedLines = patch.patched_code.split("\n")

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-gray-800/40"
        onClick={() => setExpanded(!expanded)}
      >
        {patch.validated
          ? <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
          : <XCircle className="w-5 h-5 text-yellow-400 shrink-0" />}
        <span className="flex-1 text-sm text-white">{patch.file_path}</span>
        <span className="text-xs text-gray-500 font-mono">{patch.vuln_type}</span>
        {patch.validated
          ? <span className="text-xs text-green-400 bg-green-900/30 border border-green-800 px-2 py-0.5 rounded">Verified ✓</span>
          : <span className="text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-800 px-2 py-0.5 rounded">Needs review</span>}
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>

      {expanded && (
        <div className="border-t border-gray-800">
          <div className="grid grid-cols-2 divide-x divide-gray-800">
            <div className="p-4">
              <div className="text-xs text-red-400 mb-2 font-mono">— Original (vulnerable)</div>
              <pre className="text-xs text-red-300 overflow-x-auto">
                {origLines.map((line, i) => (
                  <div key={i} className="px-2 py-0.5 bg-red-900/20 rounded mb-0.5">- {line}</div>
                ))}
              </pre>
            </div>
            <div className="p-4">
              <div className="text-xs text-green-400 mb-2 font-mono">+ Patched (secure)</div>
              <pre className="text-xs text-green-300 overflow-x-auto">
                {patchedLines.map((line, i) => (
                  <div key={i} className="px-2 py-0.5 bg-green-900/20 rounded mb-0.5">+ {line}</div>
                ))}
              </pre>
            </div>
          </div>
          {patch.validation_notes && (
            <div className="px-5 py-3 border-t border-gray-800 text-xs text-gray-400">
              {patch.validation_notes}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
