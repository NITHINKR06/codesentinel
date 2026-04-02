"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { startScan, uploadZip } from "@/lib/api"

type Mode = "github" | "url" | "zip"

export default function HomePage() {
  const router = useRouter()
  const [mode, setMode] = useState<Mode>("github")
  const [input, setInput] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleScan() {
    if (!input && !file) return
    setError("")
    setLoading(true)
    try {
      let result
      if (mode === "zip" && file) {
        result = await uploadZip(file)
      } else if (mode === "github") {
        result = await startScan(input, undefined)
      } else {
        result = await startScan(undefined, input)
      }
      router.push(`/scan/${result.scan_id}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Scan failed")
    } finally {
      setLoading(false)
    }
  }

  const handleModeChange = (next: Mode) => {
    setMode(next)
    setInput("")
    setFile(null)
  }

  return (
    <main className="bg-background text-on-background font-[Inter] min-h-screen overflow-hidden flex flex-col">
      {/* Top nav */}
      <header className="bg-[#131313] text-[#98CBFF] font-['Space_Grotesk'] text-sm tracking-tight fixed top-0 w-full flex justify-between items-center px-6 py-3 h-16 z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-[#98CBFF]">CodeSentinel</span>
          <nav className="hidden md:flex gap-6 items-center">
            <span className="text-[#98CBFF] font-bold border-b-2 border-[#98CBFF] px-2 py-1">Dashboard</span>
            <span className="text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors px-2 py-1 rounded-sm">Telemetry</span>
            <span className="text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors px-2 py-1 rounded-sm">Threat Map</span>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden sm:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
            <input
              className="bg-[#1c1b1b] border-none text-xs w-64 pl-10 pr-4 py-2 rounded-sm focus:ring-1 focus:ring-primary font-mono"
              placeholder="Global Identifier Search..."
              type="text"
            />
          </div>
          <div className="flex gap-2">
            <button className="p-2 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors rounded-sm">
              <span className="material-symbols-outlined">sensors</span>
            </button>
            <button className="p-2 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors rounded-sm">
              <span className="material-symbols-outlined">account_circle</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-16">
        {/* Sidebar */}
        <aside className="hidden md:flex flex-col h-[calc(100vh-64px)] w-64 bg-[#1C1B1B] text-[#98CBFF] text-xs uppercase tracking-widest font-semibold border-r border-[#88919D]/15 shadow-[4px_0_24px_rgba(152,203,255,0.05)]">
          <div className="p-6 border-b border-[#88919D]/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-sm bg-primary/10 border border-primary/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
                  security
                </span>
              </div>
              <div>
                <div className="text-[10px] text-primary/70 mb-0.5">CodeSentinel Ops</div>
                <div className="text-[9px] text-on-surface/50 tracking-[0.2em]">Level 4 Clearance</div>
              </div>
            </div>
          </div>
          <nav className="flex-1 py-4">
            <div className="space-y-1 px-3">
              {[
                { label: "Dashboard", icon: "dashboard" },
                { label: "Active Scans", icon: "radar" },
                { label: "Red Team Reports", icon: "security" },
                { label: "Blue Team Reports", icon: "shield" },
                { label: "Settings", icon: "settings" },
              ].map(item => (
                <button
                  key={item.label}
                  className="flex w-full items-center gap-3 px-4 py-3 rounded-sm text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:opacity-100 transition-all"
                  type="button"
                >
                  <span className="material-symbols-outlined text-lg">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </nav>
          <div className="p-4 space-y-1 border-t border-[#88919D]/10">
            <button className="flex items-center gap-3 px-4 py-2 rounded-sm text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:opacity-100 transition-all" type="button">
              <span className="material-symbols-outlined text-lg">help_center</span>
              <span>Support</span>
            </button>
            <button className="flex items-center gap-3 px-4 py-2 rounded-sm text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:opacity-100 transition-all" type="button">
              <span className="material-symbols-outlined text-lg">terminal</span>
              <span>Logs</span>
            </button>
          </div>
        </aside>

        {/* Main tactical canvas */}
        <section className="flex-1 relative overflow-hidden grid-bg flex items-center justify-center p-6">
          {/* Background topo lines */}
          <div className="absolute inset-0 opacity-20 pointer-events-none overflow-hidden">
            <svg className="absolute w-[200%] h-[200%] -top-1/2 -left-1/2" preserveAspectRatio="none" viewBox="0 0 100 100">
              {[20, 40, 60, 80].map(y => (
                <path
                  key={y}
                  d={`M0 ${y} Q 25 ${y - 10} 50 ${y} T 100 ${y}`}
                  fill="none"
                  stroke="#98CBFF"
                  strokeWidth="0.1"
                />
              ))}
            </svg>
          </div>

          <div className="w-full max-w-5xl z-10 space-y-8">
            <div className="text-center space-y-2">
              <h1 className="font-['Space_Grotesk'] text-4xl md:text-5xl font-extrabold tracking-tighter text-on-surface uppercase">
                Initialize Tactical Scan
              </h1>
              <p className="font-mono text-primary/60 text-xs uppercase tracking-widest">
                Awaiting Parameter Input // System Status: Ready
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-1 items-stretch">
              {/* Mode column */}
              <div className="md:col-span-4 bg-[#1c1b1b] border border-[#3f4852]/40 p-6 flex flex-col justify-between">
                <div className="space-y-6">
                  <h3 className="font-['Space_Grotesk'] font-bold text-xs tracking-widest text-on-surface-variant uppercase">
                    Scan Mode
                  </h3>
                  <div className="space-y-3">
                    <button
                      type="button"
                      onClick={() => handleModeChange("github")}
                      className={`w-full flex items-center justify-between p-4 text-left transition-all group border-l-4 ${
                        mode === "github"
                          ? "bg-[#2a2a2a] border-primary text-primary"
                          : "bg-[#201f1f] border-transparent text-on-surface/60 hover:text-on-surface"
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <span className="material-symbols-outlined">hub</span>
                        <div className="font-['Space_Grotesk'] font-semibold text-sm uppercase">GitHub Repository</div>
                      </div>
                      <span className="material-symbols-outlined text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                        chevron_right
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleModeChange("url")}
                      className={`w-full flex items-center justify-between p-4 text-left transition-all group ${
                        mode === "url"
                          ? "bg-[#2a2a2a] text-on-surface"
                          : "bg-[#201f1f] text-on-surface/40 hover:text-on-surface"
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <span className="material-symbols-outlined">public</span>
                        <div className="font-['Space_Grotesk'] font-semibold text-sm uppercase">Live URL Target</div>
                      </div>
                      <span className="material-symbols-outlined text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                        chevron_right
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleModeChange("zip")}
                      className={`w-full flex items-center justify-between p-4 text-left transition-all group ${
                        mode === "zip"
                          ? "bg-[#2a2a2a] text-on-surface"
                          : "bg-[#201f1f] text-on-surface/40 hover:text-on-surface"
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <span className="material-symbols-outlined">upload_file</span>
                        <div className="font-['Space_Grotesk'] font-semibold text-sm uppercase">Artifact Upload</div>
                      </div>
                      <span className="material-symbols-outlined text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                        chevron_right
                      </span>
                    </button>
                  </div>
                </div>
                <div className="mt-12 p-4 bg-[#0e0e0e] border-l border-[#2ae500]/40">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-[#2ae500] animate-pulse" />
                    <span className="font-mono text-[10px] text-[#2ae500] uppercase">Deep Analysis Engine V4.2</span>
                  </div>
                  <p className="text-[10px] text-on-surface/40 leading-relaxed">
                    Ready to intercept and analyze code vulnerabilities, secret exposures, and infrastructure-as-code
                    misconfigurations.
                  </p>
                </div>
              </div>

              {/* Input / status column */}
              <div className="md:col-span-8 bg-[#201f1f] flex flex-col">
                <div className="flex-1 p-8 space-y-12">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="font-['Space_Grotesk'] font-bold text-xs tracking-widest text-on-surface uppercase">
                        Repository Endpoint
                      </label>
                      <span className="font-mono text-[10px] text-outline uppercase">Auth Required: Optional</span>
                    </div>
                    <div className="relative">
                      {mode !== "zip" ? (
                        <input
                          className="w-full bg-[#1c1b1b] p-6 font-mono text-primary text-sm md:text-lg border-none focus:ring-0 peer placeholder:text-outline/30"
                          placeholder={
                            mode === "github" ? "https://github.com/org/repository" : "https://your-production-url.com"
                          }
                          value={input}
                          onChange={e => setInput(e.target.value)}
                          onKeyDown={e => e.key === "Enter" && handleScan()}
                        />
                      ) : (
                        <label className="block w-full">
                          <div className="border-2 border-dashed border-outline-variant/40 rounded-sm p-6 text-center cursor-pointer hover:border-primary transition-colors">
                            <span className="material-symbols-outlined text-outline mb-2 block">upload_file</span>
                            <p className="text-on-surface/60 text-sm">
                              {file ? file.name : "Click to upload repository .zip"}
                            </p>
                          </div>
                          <input
                            type="file"
                            accept=".zip"
                            className="hidden"
                            onChange={e => setFile(e.target.files?.[0] || null)}
                          />
                        </label>
                      )}
                      <div className="absolute bottom-0 left-0 h-[2px] bg-outline-variant w-full peer-focus:bg-primary transition-all" />
                    </div>
                    {error && (
                      <div className="text-xs text-secondary mt-1 font-mono">{error}</div>
                    )}
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer group">
                        <input
                          type="checkbox"
                          className="form-checkbox bg-[#2a2a2a] border-outline-variant rounded-sm text-primary focus:ring-0"
                        />
                        <span className="text-[10px] text-on-surface/60 uppercase font-['Space_Grotesk'] tracking-tighter group-hover:text-primary transition-colors">
                          Private Repository
                        </span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer group">
                        <input
                          type="checkbox"
                          defaultChecked
                          className="form-checkbox bg-[#2a2a2a] border-outline-variant rounded-sm text-primary focus:ring-0"
                        />
                        <span className="text-[10px] text-on-surface/60 uppercase font-['Space_Grotesk'] tracking-tighter group-hover:text-primary transition-colors">
                          Recursive Scan
                        </span>
                      </label>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-[#2a2a2a] p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-primary">radar</span>
                        <span className="font-['Space_Grotesk'] font-bold text-[10px] uppercase tracking-widest">
                          Active Listeners
                        </span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="font-mono text-[10px] text-on-surface/50">
                          SEC-CORE: <span className="text-[#2ae500]">ON</span>
                        </span>
                        <span className="font-mono text-[10px] text-on-surface/50">
                          GEO-FILTER: <span className="text-on-surface/30">OFF</span>
                        </span>
                      </div>
                    </div>
                    <div className="bg-[#2a2a2a] p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-primary">memory</span>
                        <span className="font-['Space_Grotesk'] font-bold text-[10px] uppercase tracking-widest">
                          Resource Allocation
                        </span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="font-mono text-[10px] text-on-surface/50">CPU: 4 THREADS</span>
                        <span className="font-mono text-[10px] text-on-surface/50">TIMEOUT: 300s</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action bar */}
                <div className="p-8 bg-[#2a2a2a]/70 flex flex-col sm:flex-row items-center justify-between gap-6 border-t border-[#3f4852]/30">
                  <div className="flex flex-col gap-1">
                    <span className="font-['Space_Grotesk'] text-xs font-bold uppercase">Estimated Triage Time</span>
                    <span className="font-mono text-xl text-primary">
                      02:45
                      <small className="text-xs ml-1 opacity-50">MM:SS</small>
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={handleScan}
                    disabled={loading || (!input && !file)}
                    className="relative bg-primary text-on-primary font-['Space_Grotesk'] font-extrabold text-sm uppercase tracking-[0.2em] px-10 py-5 rounded-sm transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed glow-button"
                  >
                    <span className="relative z-10 flex items-center gap-3">
                      {loading ? "Initializing..." : "Initiate Scan"}
                      <span className="material-symbols-outlined text-lg">double_arrow</span>
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {/* Footer stats */}
            <div className="flex flex-wrap justify-center gap-12 pt-8">
              <div className="flex flex-col items-center gap-1">
                <span className="text-on-surface/40 uppercase text-[9px] font-['Space_Grotesk'] tracking-widest">
                  Total Repos Analyzed
                </span>
                <span className="font-mono text-lg text-primary">1,240,932</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <span className="text-on-surface/40 uppercase text-[9px] font-['Space_Grotesk'] tracking-widest">
                  Vulnerabilities Patched
                </span>
                <span className="font-mono text-lg text-[#2ae500]">42,881</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <span className="text-on-surface/40 uppercase text-[9px] font-['Space_Grotesk'] tracking-widest">
                  Active Operators
                </span>
                <span className="font-mono text-lg text-on-surface">14</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full bg-[#1C1B1B] text-[#98CBFF] flex justify-around items-center h-16 px-4 z-50">
        <button className="flex flex-col items-center gap-1 opacity-60" type="button">
          <span className="material-symbols-outlined text-lg">dashboard</span>
          <span className="text-[9px] uppercase font-bold">Dash</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-[#98CBFF] border-t-2 border-[#98CBFF] pt-1" type="button">
          <span className="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
            radar
          </span>
          <span className="text-[9px] uppercase font-bold">Scan</span>
        </button>
        <button className="flex flex-col items-center gap-1 opacity-60" type="button">
          <span className="material-symbols-outlined text-lg">security</span>
          <span className="text-[9px] uppercase font-bold">Threats</span>
        </button>
        <button className="flex flex-col items-center gap-1 opacity-60" type="button">
          <span className="material-symbols-outlined text-lg">settings</span>
          <span className="text-[9px] uppercase font-bold">Settings</span>
        </button>
      </nav>
    </main>
  )
}
