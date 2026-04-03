export type Severity = "critical" | "high" | "medium" | "low"

export interface Finding {
  id: string
  vuln_type: string
  severity: Severity
  file_path: string
  line_number: number
  function_name?: string
  title: string
  description: string
  plain_impact: string
  vulnerable_code?: string
  poc_exploit?: string
  mitre_technique?: string
  mitre_tactic?: string
}

export interface Chain {
  chain_id: string
  nodes: string[]
  vulns: Finding[]
  length: number
  escalated_severity: Severity
  attack_narrative: string
}

export interface Patch {
  finding_id: string
  file_path: string
  vuln_type: string
  original_code: string
  patched_code: string
  validated: boolean
  validation_attempts: number
  validation_notes?: string
  applied_to_pr: boolean
}

export interface GhostCommit {
  commit_sha: string
  commit_message: string
  author: string
  committed_at: string
  file: string
  secret_type: string
  secret_preview: string
  still_present: boolean
  severity: Severity
  title: string
  plain_impact: string
}

export interface ThreatActor {
  name: string
  aliases: string[]
  origin: string
  motivation: string
  targets: string[]
  known_attacks: string[]
  risk_level: string
  match_score: number
  matched_vulns: string[]
  match_explanation: string
}

export interface GraphNode {
  id: string
  label: string
  file: string
  hasVuln: boolean
  severity?: Severity
  inChain: boolean
  vulns: Finding[]
}

export interface GraphEdge {
  source: string
  target: string
}

export interface SimulationObservation {
  step: number
  action: string
  payload_name: string
  request?: Record<string, unknown>
  result: Record<string, unknown>
  verdict: Record<string, unknown>
}

export interface SimulationResult {
  vuln_type: string
  file_path: string
  confirmed: boolean
  evidence?: string
  payload_name?: string
  target_id?: string
  target_url?: string
  observations?: SimulationObservation[]
  confirmation_message?: string
  executed?: boolean
  output?: string
  duration_ms?: number
  simulation_notes?: string
}

export interface AttackGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
  // The backend stores extra metadata in the same JSON blob.
  simulations?: SimulationResult[]
  narrative?: string
  recon?: Record<string, unknown>
}

export interface ScanReport {
  scan_id: string
  status: string
  repo_name?: string
  github_url?: string
  score_before?: number
  score_after?: number
  total_findings: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  findings: Finding[]
  chains: Chain[]
  patches: Patch[]
  ghost_commits: GhostCommit[]
  threat_actor?: ThreatActor
  attack_graph?: AttackGraph
  pr_url?: string
  completed_at?: string
}

export interface ScanEvent {
  scan_id: string
  stage: string
  message: string
  progress: number
  data?: Record<string, unknown>
}
