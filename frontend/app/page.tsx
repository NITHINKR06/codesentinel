"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { startScan, uploadZip } from "@/lib/api"
import { Shield, Github, Globe, Upload, AlertCircle } from "lucide-react"

export default function HomePage() {
  const router = useRouter()
  const [mode, setMode] = useState<"github" | "url" | "zip">("github")
  const [input, setInput] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleScan() {
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

  return (
    <main className="min-h-screen bg-gray-950 flex flex-col items-center justify-center px-4">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Shield className="w-10 h-10 text-red-400" />
          <h1 className="text-4xl font-bold text-white tracking-tight">CodeSentinel</h1>
        </div>
        <p className="text-gray-400 text-lg max-w-xl">
          Find vulnerabilities. Prove them real. Fix them automatically.
        </p>
        <div className="flex gap-6 justify-center mt-4 text-sm text-gray-500">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"/>Red: find &amp; exploit</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block"/>Blue: patch &amp; verify</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block"/>Score: before &amp; after</span>
        </div>
      </div>

      {/* Card */}
      <div className="w-full max-w-xl bg-gray-900 border border-gray-800 rounded-2xl p-8">
        {/* Mode tabs */}
        <div className="flex gap-2 mb-6">
          {([
            { key: "github", label: "GitHub URL", icon: Github },
            { key: "url", label: "Live URL", icon: Globe },
            { key: "zip", label: "Upload ZIP", icon: Upload },
          ] as const).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => { setMode(key); setInput(""); setFile(null) }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm transition-all ${
                mode === key
                  ? "bg-gray-700 text-white border border-gray-600"
                  : "text-gray-500 hover:text-gray-300 border border-transparent"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Input */}
        {mode !== "zip" ? (
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-gray-500 mb-4"
            placeholder={mode === "github" ? "https://github.com/user/repo" : "https://your-app.com"}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleScan()}
          />
        ) : (
          <label className="block w-full mb-4">
            <div className="border-2 border-dashed border-gray-700 rounded-xl p-6 text-center cursor-pointer hover:border-gray-500 transition-colors">
              <Upload className="w-6 h-6 text-gray-500 mx-auto mb-2" />
              <p className="text-gray-400 text-sm">{file ? file.name : "Click to upload .zip"}</p>
            </div>
            <input type="file" accept=".zip" className="hidden" onChange={e => setFile(e.target.files?.[0] || null)} />
          </label>
        )}

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm mb-4">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <button
          onClick={handleScan}
          disabled={loading || (!input && !file)}
          className="w-full bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium py-3 rounded-xl transition-colors text-sm"
        >
          {loading ? "Starting scan..." : "Scan Now"}
        </button>
      </div>

      {/* Stats row */}
      <div className="flex gap-8 mt-10 text-center">
        {[
          { label: "Vuln types detected", value: "12+" },
          { label: "PoC exploits generated", value: "Auto" },
          { label: "Patches verified", value: "Red ✓" },
        ].map(({ label, value }) => (
          <div key={label}>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-xs text-gray-500 mt-1">{label}</div>
          </div>
        ))}
      </div>
    </main>
  )
}
