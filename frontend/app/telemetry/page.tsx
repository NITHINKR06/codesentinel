import Link from "next/link"
import OpsSidebar from "@/components/OpsSidebar"

export default function TelemetryPage() {
  return (
    <main className="bg-background text-on-background min-h-screen overflow-hidden flex flex-col font-[Inter]">
      <header className="bg-[#131313] text-[#98CBFF] font-['Space_Grotesk'] text-sm tracking-tight fixed top-0 w-full flex justify-between items-center px-6 py-3 h-16 z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-[#98CBFF]">CodeSentinel</span>
          <nav className="hidden md:flex gap-6 items-center">
            <Link href="/dashboard" className="text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors px-2 py-1 rounded-sm">Dashboard</Link>
            <span className="text-[#98CBFF] font-bold border-b-2 border-[#98CBFF] px-2 py-1">Telemetry</span>
            <Link href="/threat-map" className="text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors px-2 py-1 rounded-sm">Threat Map</Link>
          </nav>
        </div>
      </header>

      <div className="flex flex-1 pt-16">
        <OpsSidebar active="dashboard" className="hidden md:flex h-[calc(100vh-64px)] w-64" />

        <section className="flex-1 relative overflow-y-auto grid-bg p-6">
          <div className="w-full max-w-4xl mx-auto space-y-4">
            <h1 className="font-['Space_Grotesk'] text-2xl md:text-3xl font-extrabold tracking-tighter text-on-surface uppercase">
              Telemetry
            </h1>
            <p className="font-mono text-primary/60 text-[10px] uppercase tracking-widest">
              System-wide scan metrics and streaming data (coming soon)
            </p>
            <div className="mt-6 bg-surface-container-low border border-outline-variant/20 rounded-sm p-6 text-sm text-on-surface-variant">
              Live telemetry dashboards will appear here in a future version.
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
