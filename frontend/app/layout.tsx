import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "CodeSentinel — Automated Security Analysis",
  description: "Find vulnerabilities, prove them real, fix them automatically.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
