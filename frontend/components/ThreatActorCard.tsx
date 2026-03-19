"use client"
import { ThreatActor } from "@/types"
import { AlertTriangle, Target, Zap } from "lucide-react"

const RISK_STYLES: Record<string, string> = {
  critical: "border-red-800 bg-red-950/30",
  high: "border-orange-800 bg-orange-950/20",
  medium: "border-yellow-800 bg-yellow-950/20",
}

export default function ThreatActorCard({ actor }: { actor: ThreatActor }) {
  return (
    <div className={`border rounded-xl p-5 mb-6 ${RISK_STYLES[actor.risk_level] || RISK_STYLES.medium}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <div>
            <div className="text-white font-semibold">{actor.name}</div>
            <div className="text-xs text-gray-400 mt-0.5">
              {actor.aliases.join(" · ")} — {actor.origin}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500 mb-1">Match score</div>
          <div className="text-2xl font-bold text-red-400">{actor.match_score}</div>
        </div>
      </div>

      <p className="text-sm text-gray-300 mb-4 leading-relaxed">{actor.match_explanation}</p>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
            <Target className="w-3 h-3" /> Known targets
          </div>
          <div className="flex flex-wrap gap-1.5">
            {actor.targets.map(t => (
              <span key={t} className="text-xs px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-gray-300">{t}</span>
            ))}
          </div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
            <Zap className="w-3 h-3" /> Matched vulnerabilities
          </div>
          <div className="flex flex-wrap gap-1.5">
            {actor.matched_vulns.map(v => (
              <span key={v} className="text-xs px-2 py-0.5 bg-red-900/40 border border-red-800 rounded text-red-300 font-mono">{v}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-current/20">
        <div className="text-xs text-gray-500 mb-2">Documented attacks by this group</div>
        <ul className="space-y-1">
          {actor.known_attacks.map((attack, i) => (
            <li key={i} className="text-xs text-gray-400 flex items-start gap-2">
              <span className="text-gray-600 mt-0.5">→</span>
              {attack}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
