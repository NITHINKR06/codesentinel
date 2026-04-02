# CodeSentinel Frontend Overview

## Tech stack
- Framework: Next.js 13+ (app router) with TypeScript
- Rendering: Mostly client components ("use client") with React hooks
- Styling: Tailwind CSS, dark theme (gray-950 background, card-like panels)
- Icons: lucide-react
- Data & realtime: REST API calls via `frontend/lib/api.ts`, WebSocket via `frontend/lib/socket.ts`

## High-level UX flow
- Landing (scanner entry): `frontend/app/page.tsx`
  - Lets user choose scan mode: GitHub URL, live URL, or ZIP upload.
  - Calls `startScan` or `uploadZip` from `lib/api.ts`.
  - On success, redirects to `/scan/[id]` using the returned `scan_id`.

- Live scan progress: `frontend/app/scan/[id]/page.tsx`
  - Connects to the backend WebSocket with `connectToScan` from `lib/socket.ts`.
  - Streams `ScanEvent` messages that drive:
    - A progress percentage bar
    - A current stage label (ingesting, scanning, chaining, generating, patching, validating, profiling, scoring, complete/failed)
    - A terminal-like log feed
  - On scan completion, auto-redirects to `/scan/[id]/report`.

- Red-team view: `frontend/app/scan/[id]/red/page.tsx`
  - Fetches `ScanReport` via `getReport(scanId)`.
  - Focus: attacker perspective and intelligence from `report.attack_graph` and recon data.
  - Sections (tabbed):
    - Attack Narrative (AI text or fallback auto-narrative from critical findings)
    - Recon Intel (tech stack, exposed secrets, attack surface, dependency vulns)
    - Simulations (PoC exploit simulations and confirmations)
    - Chains (multi-step exploit chains)
    - Ghost Commits (secrets in git history)

- Blue-team report: `frontend/app/scan/[id]/report/page.tsx`
  - Fetches `ScanReport` via `getReport(scanId)`.
  - Focus: defender view and remediation.
  - Core UI pieces:
    - Score comparison (before/after) using `ScoreGauge`.
    - KPIs: critical finding count, exploit chain count.
    - Threat actor summary via `ThreatActorCard`.
    - Tabs:
      - Overview: top critical findings + git history leaks summary.
      - Findings: full list of findings rendered via `FindingCard`.
      - Chains: exploit chain narratives.
      - Patches: auto-generated patches via `PatchViewer`.
      - Attack Graph: visual call/attack graph via `AttackGraph`.
  - GitHub PR integration:
    - If `report.github_url` exists, user can trigger PR creation.
    - Calls backend `POST /api/github/pr` (either from here or via `lib/api.ts`).
    - When done, shows a link to the created PR.

- Dashboard: `frontend/app/dashboard/page.tsx`
  - Uses `listScans()` to fetch recent scans.
  - Derived `scoreHistory` is passed into `ScoreHistory` to visualize scores over time.
  - Scan list cards display:
    - Repository name / GitHub URL / scan ID
    - Timestamp
    - Score before → after
    - Finding count
    - Status chip (complete, failed, pending, scanning)
  - Clicking a card navigates to either `/scan/[id]` or `/scan/[id]/report` depending on status.

## Shared components (frontend/components)
- `ScoreGauge.tsx`
  - Simple SVG circular gauge that shows a 0–100 score.
  - Color logic: green (>=80), amber (>=50), red (<50).

- `ScoreHistory.tsx`
  - Small time-series style component for historical scores (used on dashboard).

- `AttackGraph.tsx`
  - D3-based force-directed graph of the attack graph.
  - Inputs: `AttackGraph` object with `nodes` and `edges` (see `frontend/types/index.ts`).
  - Visual encodings:
    - Node color by severity (critical, high, medium, low).
    - Larger, pulsing nodes for nodes that are part of an exploit chain (`inChain`).
    - Arrow-headed edges for call/exploit direction.

- `FindingCard.tsx`
  - Renders a single finding (severity pill, file path + line, impact text, etc.).
  - Used heavily in the report findings tab.

- `ThreatActorCard.tsx`
  - Shows the matched threat actor profile from the report.
  - Includes name, description, and match score.

- `PatchViewer.tsx`
  - Shows patch data from `report.patches` (diff-style view).

- `LiveFeed.tsx`
  - (If present) likely a reusable live-stream/log component used by scan progress.

- `ExploitViewer.tsx`
  - For showing PoC exploit payloads / outputs where needed.

## Data models & types
- Types live in `frontend/types/index.ts`:
  - `ScanEvent` — events streamed over WebSocket during a scan.
  - `ScanReport` — full aggregated report used in red/blue views.
  - `AttackGraph`, `GraphNode` — graph data for the attack visualization.

## API and realtime layer
- `frontend/lib/api.ts`
  - `startScan(githubUrl?, liveUrl?)` → POST `/api/scan`
  - `uploadZip(file)` → POST multipart `/api/scan/upload`
  - `getScan(scanId)` → GET `/api/scan/{id}`
  - `getReport(scanId)` → GET `/api/report/{id}`
  - `listScans()` → GET `/api/scan/`
  - `createPR(scanId, githubToken, repoUrl)` → POST `/api/github/pr`
  - `getBadgeUrl(scanId)` → URL helper for badge endpoint.

- `frontend/lib/socket.ts`
  - `connectToScan(scanId, onMessage, onComplete, onError)`
  - Wraps browser `WebSocket` to subscribe to a scan-specific channel and emit `ScanEvent`s to the UI.

## Layout, routing & theming
- Layout: `frontend/app/layout.tsx`
  - Global font and Tailwind styles via `app/globals.css`.
  - Dark, dashboard-style look: cards on gray-950 background.

- Routes:
  - `/` — landing / start scan.
  - `/dashboard` — list of scans and score history.
  - `/scan/[id]` — live scan progress and log.
  - `/scan/[id]/report` — blue-team report (defensive, scoring, patches).
  - `/scan/[id]/red` — red-team report (offensive, narrative, recon).

## Design patterns to keep in mind for redesign
- Clear separation of concerns:
  - Pages focus on layout, tab state, and data loading.
  - Components encapsulate visualization (gauges, graphs, cards).
- Consistent red/blue theming:
  - Red team views use red accents and monospaced text for a "terminal" feel.
  - Blue team views use mixed gray/blue accents and more dashboard-like typography.
- Real-time feedback:
  - Progress bar + terminal log keep the user engaged while scanning.
  - Automatic transition from scan → report.
- Security storytelling:
  - Red view: attack narrative and attacker POV.
  - Blue view: remediation KPIs and patches.

> You can use this document as a map of existing flows and components when redesigning the UI/UX (e.g., consolidating navigation, harmonizing spacing/typography, or adding more visual hierarchy around scores, chains, and patches).
