"use client"

import Link from "next/link"
import OpsSidebar from "@/components/OpsSidebar"

export default function NotFoundPage() {
  return (
    <main className="bg-background text-on-background min-h-screen overflow-hidden flex flex-col font-[Inter]">
      {/* Top nav */}
      <header className="bg-[#131313] text-[#98CBFF] font-['Space_Grotesk'] text-sm tracking-tight fixed top-0 w-full flex justify-between items-center px-6 py-3 h-16 z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-[#98CBFF]">CodeSentinel</span>
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
            <button className="p-2 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors rounded-sm" type="button">
              <span className="material-symbols-outlined">sensors</span>
            </button>
            <button className="p-2 hover:bg-[#2A2A2A] hover:text-[#98CBFF] transition-colors rounded-sm" type="button">
              <span className="material-symbols-outlined">account_circle</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-16">
        <OpsSidebar active="dashboard" className="hidden md:flex h-[calc(100vh-64px)] w-64" />

        {/* Main 404 canvas */}
        <section className="flex-1 relative overflow-hidden grid-bg flex items-center justify-center p-6">
          {/* Soft glow background */}
          <div className="absolute inset-0 opacity-20 pointer-events-none overflow-hidden">
            <div className="absolute -top-1/4 -right-1/4 w-80 h-80 bg-primary blur-[120px] rounded-full" />
            <div className="absolute -bottom-1/4 -left-1/4 w-80 h-80 bg-secondary blur-[120px] rounded-full" />
          </div>

          <div className="relative z-10 w-full max-w-xl bg-surface-container-low border border-outline-variant/30 rounded-sm p-8 flex flex-col gap-6">
            <div className="flex items-center gap-3 text-secondary">
              <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                warning
              </span>
              <div className="flex flex-col">
                <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-secondary/80">
                  Navigation Anomaly Detected
                </span>
                <h1 className="font-['Space_Grotesk'] text-3xl font-extrabold tracking-tighter text-on-surface">
                  404 // Zone Not Found
                </h1>
              </div>
            </div>

            <p className="font-mono text-xs text-on-surface/70 leading-relaxed">
              The resource you requested is outside the mapped operations grid. It may have been moved, secured, or
              never deployed. Choose a safe extraction point below to re-enter the CodeSentinel console.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
              <Link
                href="/"
                className="bg-primary text-on-primary font-['Space_Grotesk'] text-xs font-bold uppercase tracking-[0.2em] px-4 py-3 rounded-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all"
              >
                <span className="material-symbols-outlined text-base">radar</span>
                <span>Initiate New Scan</span>
              </Link>
              <Link
                href="/dashboard"
                className="bg-surface-container-high border border-outline-variant/40 text-on-surface font-['Space_Grotesk'] text-xs font-bold uppercase tracking-[0.2em] px-4 py-3 rounded-sm flex items-center justify-center gap-2 hover:border-primary hover:text-primary transition-all"
              >
                <span className="material-symbols-outlined text-base">dashboard</span>
                <span>Back To Dashboard</span>
              </Link>
            </div>

            <div className="mt-4 border-t border-outline-variant/20 pt-4 flex items-center justify-between text-[10px] font-mono text-on-surface/50">
              <span>
                Trace ID: <span className="text-primary">CS-{Math.random().toString(36).slice(2, 8).toUpperCase()}</span>
              </span>
              <span className="hidden sm:inline">If this persists, contact an operator.</span>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
