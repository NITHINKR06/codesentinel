import Link from "next/link"

export default function NotFoundPage() {
  return (
    <main className="bg-background text-on-surface font-body min-h-screen flex">
      {/* Side navigation (404 variant) */}
      <aside className="hidden md:flex flex-col h-screen w-64 left-0 top-0 fixed bg-[#1C1B1B] border-r border-[#E5E2E1]/10 shadow-[4px_0_24px_rgba(152,203,255,0.05)] z-50">
        <div className="px-6 py-8">
          <div className="font-['Space_Grotesk'] text-[#98CBFF] font-bold uppercase tracking-widest text-lg">
            CodeSentinel
          </div>
          <div className="mt-1 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-error animate-pulse" />
            <span className="text-[10px] uppercase tracking-tighter opacity-60">Level 4 Clearance</span>
          </div>
        </div>
        <div className="px-4 mb-6">
          <Link
            href="/"
            className="w-full inline-flex justify-center py-2 bg-primary text-on-primary font-mono text-xs font-bold rounded-sm active:scale-95 transition-all"
          >
            New Scan
          </Link>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all duration-200 ease-in-out text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:text-[#E5E2E1]"
          >
            <span className="material-symbols-outlined text-[20px]">grid_view</span>
            <span className="font-['Inter'] text-sm">Dashboard</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all duration-200 ease-in-out text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:text-[#E5E2E1]"
          >
            <span className="material-symbols-outlined text-[20px]">radar</span>
            <span className="font-['Inter'] text-sm">Threat Hunt</span>
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all duration-200 ease-in-out text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:text-[#E5E2E1]"
          >
            <span className="material-symbols-outlined text-[20px]">terminal</span>
            <span className="font-['Inter'] text-sm">Logs</span>
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all duration-200 ease-in-out text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:text-[#E5E2E1]"
          >
            <span className="material-symbols-outlined text-[20px]">hub</span>
            <span className="font-['Inter'] text-sm">Network</span>
          </Link>
          <Link
            href="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all duration-200 ease-in-out text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:text-[#E5E2E1]"
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
            <span className="font-['Inter'] text-sm">Settings</span>
          </Link>
        </nav>
        <div className="p-4 border-t border-[#E5E2E1]/5">
          <div className="flex items-center gap-3 px-3 py-2 text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] rounded-sm cursor-pointer transition-all">
            <span className="material-symbols-outlined text-[20px]">help</span>
            <span className="font-['Inter'] text-sm">Support</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] rounded-sm cursor-pointer transition-all">
            <span className="material-symbols-outlined text-[20px]">description</span>
            <span className="font-['Inter'] text-sm">Documentation</span>
          </div>
        </div>
      </aside>

      {/* Main canvas */}
      <main className="flex-1 md:ml-64 flex flex-col relative overflow-hidden">
        {/* Top nav */}
        <header className="w-full top-0 sticky z-40 bg-[#131313] flex justify-between items-center px-6 py-3">
          <div className="flex items-center gap-8">
            <span className="md:hidden font-['Space_Grotesk'] text-xl font-bold tracking-tighter text-[#98CBFF]">
              CodeSentinel
            </span>
            <nav className="hidden md:flex gap-6">
              <span className="font-['Space_Grotesk'] tracking-tight text-[#E5E2E1] opacity-70 hover:text-[#98CBFF] hover:bg-[#2A2A2A] transition-colors px-2 py-1 rounded-sm">
                Operations
              </span>
              <span className="font-['Space_Grotesk'] tracking-tight text-[#E5E2E1] opacity-70 hover:text-[#98CBFF] hover:bg-[#2A2A2A] transition-colors px-2 py-1 rounded-sm">
                Telemetry
              </span>
              <span className="font-['Space_Grotesk'] tracking-tight text-[#E5E2E1] opacity-70 hover:text-[#98CBFF] hover:bg-[#2A2A2A] transition-colors px-2 py-1 rounded-sm">
                Nodes
              </span>
              <span className="font-['Space_Grotesk'] tracking-tight text-[#E5E2E1] opacity-70 hover:text-[#98CBFF] hover:bg-[#2A2A2A] transition-colors px-2 py-1 rounded-sm">
                Vault
              </span>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center bg-[#1C1B1B] rounded-sm px-3 py-1.5 border border-outline-variant/20">
              <span className="material-symbols-outlined text-sm opacity-50 mr-2">search</span>
              <input
                className="bg-transparent border-none focus:ring-0 text-xs font-mono p-0 w-32 placeholder:opacity-30"
                placeholder="Access ID..."
                type="text"
              />
            </div>
            <div className="flex gap-2">
              <button className="p-2 text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] rounded-sm transition-all active:scale-95" type="button">
                <span className="material-symbols-outlined">notifications</span>
              </button>
              <button className="p-2 text-[#E5E2E1] opacity-70 hover:bg-[#2A2A2A] rounded-sm transition-all active:scale-95" type="button">
                <span className="material-symbols-outlined">terminal</span>
              </button>
            </div>
            <div className="h-8 w-8 rounded-full bg-surface-container-high border border-primary/20 flex items-center justify-center overflow-hidden">
              <img
                alt="Operator Profile"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuA77H_ObmShWGnRvQ4XFqOjqCfxoRJOOuRAuEtKcq53W-TFFUXr3kuaZeFKj8HWf-Xx2R7DFopnuGTjKXDO0Q5-uNpmI4eup_0tQH8WnIzDLy-aIyxdmnwFAwLkAIWOoFKryaLEcjMDS17T2F_sR2uV9Dja32H2K4DHScNAEBRWQtNL1EZFPG0QeHVyHyPYm6_w8RD-RSrCo7F92XtRL1DuUcX-lKdTf4OVOmmyPtBGrCfILXvgobhPmm6jyFka2qUvxqMeu7FXuZoF"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </header>

        {/* 404 content */}
        <div className="flex-1 relative flex flex-col items-center justify-center p-8">
          {/* Background grid + oscilloscope */}
          <div className="absolute inset-0 grid-noise opacity-30 pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-full h-32 opacity-20 pointer-events-none overflow-hidden">
            <svg className="w-full h-full" viewBox="0 0 1000 100">
              <path
                className="oscilloscope-path"
                d="M0,50 L50,50 L60,20 L70,80 L80,50 L150,50 L160,10 L180,90 L200,50 L300,50 L310,30 L325,70 L340,50 L500,50 L510,5 L530,95 L550,50 L700,50 L715,40 L730,60 L745,50 L1000,50"
                fill="none"
                stroke="#98CBFF"
                strokeWidth="1"
              />
            </svg>
          </div>

          <div className="z-10 flex flex-col md:flex-row items-center gap-12 max-w-6xl w-full">
            {/* Left: big 404 + text */}
            <div className="flex-1 flex flex-col items-center md:items-start">
              <div className="relative group">
                <h1 className="text-[6rem] md:text-[10rem] lg:text-[12rem] xl:text-[18rem] font-headline font-extrabold leading-none tracking-tighter text-surface-container-high select-none glitch-text">
                  404
                </h1>
                <div className="absolute top-1/4 left-0 w-3/4 h-8 bg-background border-y border-secondary opacity-80 mix-blend-difference" />
                <div className="absolute bottom-1/3 right-0 w-1/2 h-12 bg-background border-y border-primary opacity-80 mix-blend-difference" />
              </div>

              <div className="mt-8 space-y-4 text-center md:text-left">
                <h2 className="text-3xl md:text-5xl font-headline font-bold text-secondary uppercase tracking-tight">
                  SIGNAL INTERRUPTED: NODE NOT FOUND
                </h2>
                <p className="text-on-surface-variant max-w-xl text-lg font-body leading-relaxed">
                  The requested intelligence asset is currently <span className="bg-on-surface text-background px-1">off-grid</span> or has been
                  neutralized by defensive protocols. Verify terminal coordinates and re-establish handshake.
                </p>
              </div>

              <div className="mt-12 flex flex-col sm:flex-row gap-4">
                <Link
                  href="/"
                  className="px-8 py-4 bg-primary text-on-primary font-mono font-bold text-sm tracking-widest flex items-center gap-3 hover:bg-primary-container transition-all active:scale-95 group"
                >
                  <span className="material-symbols-outlined group-hover:rotate-180 transition-transform">refresh</span>
                  RE-INITIALIZE UPLINK
                </Link>
                <Link
                  href="/settings"
                  className="px-8 py-4 border border-outline/20 text-on-surface font-mono text-sm tracking-widest hover:bg-surface-container-high transition-all flex items-center justify-center"
                >
                  SYSTEM DIAGNOSTIC
                </Link>
              </div>
            </div>

            {/* Right: error log panel */}
            <aside className="w-full md:w-80 h-96 bg-surface-container-lowest border border-outline-variant/10 flex flex-col shadow-2xl relative">
              <div className="px-4 py-3 bg-surface-container-low border-b border-outline-variant/10 flex justify-between items-center">
                <span className="text-[10px] font-mono text-primary uppercase tracking-widest">Live Error Feed</span>
                <span className="text-[10px] font-mono text-error uppercase animate-pulse">Critical</span>
              </div>
              <div className="flex-1 overflow-hidden p-4 font-mono text-[11px] space-y-3">
                <div className="text-on-tertiary-fixed-variant flex gap-2">
                  <span className="opacity-40">[14:22:01]</span>
                  <span>SYS_INIT_SEQUENCE_SUCCESS</span>
                </div>
                <div className="text-on-tertiary-fixed-variant flex gap-2">
                  <span className="opacity-40">[14:22:02]</span>
                  <span>UPLINK_ESTABLISHED_PORT_443</span>
                </div>
                <div className="text-error flex gap-2 border-l-2 border-error pl-2 bg-error/5 py-1">
                  <span className="opacity-40">[14:22:03]</span>
                  <span className="font-bold">ERR_CONNECTION_REFUSED</span>
                </div>
                <div className="text-on-surface-variant flex gap-2">
                  <span className="opacity-40">[14:22:03]</span>
                  <span>RETRY_ATTEMPT_1...</span>
                </div>
                <div className="text-error flex gap-2 border-l-2 border-error pl-2 bg-error/5 py-1">
                  <span className="opacity-40">[14:22:05]</span>
                  <span className="font-bold">NODE_UNREACHABLE_TIMEOUT</span>
                </div>
                <div className="text-secondary flex gap-2">
                  <span className="opacity-40">[14:22:06]</span>
                  <span>TRACING_HOP_FAILED_0x004F</span>
                </div>
                <div className="text-on-surface-variant flex gap-2">
                  <span className="opacity-40">[14:22:07]</span>
                  <span>RETRY_ATTEMPT_2...</span>
                </div>
                <div className="text-on-surface-variant flex gap-2">
                  <span className="opacity-40">[14:22:10]</span>
                  <span>RETRY_ATTEMPT_3...</span>
                </div>
                <div className="text-error flex gap-2 border-l-2 border-error pl-2 bg-error/5 py-1">
                  <span className="opacity-40">[14:22:15]</span>
                  <span className="font-bold">HANDSHAKE_ABORTED_SIGNAL_LOST</span>
                </div>
                <div className="text-on-surface-variant opacity-30 flex gap-2 italic">
                  <span>_listening_for_packets...</span>
                </div>
              </div>
              <div className="p-3 bg-surface-container-low border-t border-outline-variant/10 text-[9px] font-mono text-center opacity-50 uppercase tracking-tighter">
                Hardware: CS-OMEGA-7 // Buffer: 0kb
              </div>
            </aside>
          </div>
        </div>

        {/* Mobile bottom nav */}
        <nav className="md:hidden sticky bottom-0 w-full bg-[#1C1B1B] border-t border-[#E5E2E1]/10 px-6 py-3 flex justify-between items-center z-50">
          <Link href="/dashboard" className="flex flex-col items-center gap-1 text-[#E5E2E1] opacity-60">
            <span className="material-symbols-outlined">grid_view</span>
            <span className="text-[10px]">Dashboard</span>
          </Link>
          <Link href="/" className="flex flex-col items-center gap-1 text-[#E5E2E1] opacity-60">
            <span className="material-symbols-outlined">radar</span>
            <span className="text-[10px]">Hunt</span>
          </Link>
          <Link href="/dashboard" className="flex flex-col items-center gap-1 text-[#E5E2E1] opacity-60">
            <span className="material-symbols-outlined">terminal</span>
            <span className="text-[10px]">Logs</span>
          </Link>
          <Link href="/settings" className="flex flex-col items-center gap-1 text-[#E5E2E1] opacity-60">
            <span className="material-symbols-outlined">settings</span>
            <span className="text-[10px]">Settings</span>
          </Link>
        </nav>

        {/* Ambient glow */}
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none -z-10" />
        <div className="fixed -bottom-40 -right-40 w-[600px] h-[600px] bg-secondary/5 rounded-full blur-[100px] pointer-events-none -z-10" />
      </main>
    </main>
  )
}
