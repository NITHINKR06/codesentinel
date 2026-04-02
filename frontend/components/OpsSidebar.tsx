import Link from "next/link"

export type OpsSidebarActive = "dashboard" | "scan" | "red" | "blue" | "settings"

interface OpsSidebarProps {
  active?: OpsSidebarActive
  className?: string
  /** Optional scan id so nav can deep-link into a specific scan's pages */
  scanId?: string
}

export default function OpsSidebar({ active, className = "", scanId }: OpsSidebarProps) {
  const items: { key: OpsSidebarActive; label: string; icon: string; href: string }[] = [
    { key: "dashboard", label: "Dashboard", icon: "dashboard", href: "/dashboard" },
    // If we know the scan id, send Active Scans to that scan's live/logs page, otherwise to scan initializer
    { key: "scan", label: "Active Scans", icon: "radar", href: scanId ? `/scan/${scanId}` : "/" },
    // Red/Blue reports link into the current scan when scanId is provided, otherwise just land on dashboard
    { key: "red", label: "Red Team Reports", icon: "security", href: scanId ? `/scan/${scanId}/red` : "/dashboard" },
    { key: "blue", label: "Blue Team Reports", icon: "shield", href: scanId ? `/scan/${scanId}/report` : "/dashboard" },
    { key: "settings", label: "Settings", icon: "settings", href: "/settings" },
  ]

  return (
    <aside
      className={`${className} bg-[#1C1B1B] text-[#98CBFF] text-xs uppercase tracking-widest font-semibold border-r border-[#88919D]/15 shadow-[4px_0_24px_rgba(152,203,255,0.05)] flex flex-col`}
    >
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
          {items.map(item => {
            const isActive = active === item.key
            return (
              <Link
                key={item.key}
                href={item.href}
                className={`flex w-full items-center gap-3 px-4 py-3 rounded-sm text-[#E5E2E1] transition-all border-l-4 ${
                  isActive
                    ? "bg-[#201F1F] opacity-100 border-primary text-[#E5E2E1]"
                    : "opacity-60 border-transparent hover:bg-[#201F1F] hover:opacity-100"
                }`}
              >
                <span className="material-symbols-outlined text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      <div className="p-4 space-y-1 border-t border-[#88919D]/10">
        <button
          className="flex items-center gap-3 px-4 py-2 rounded-sm text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:opacity-100 transition-all"
          type="button"
        >
          <span className="material-symbols-outlined text-lg">help_center</span>
          <span>Support</span>
        </button>
        <button
          className="flex items-center gap-3 px-4 py-2 rounded-sm text-[#E5E2E1] opacity-60 hover:bg-[#201F1F] hover:opacity-100 transition-all"
          type="button"
        >
          <span className="material-symbols-outlined text-lg">terminal</span>
          <span>Logs</span>
        </button>
      </div>
    </aside>
  )
}
