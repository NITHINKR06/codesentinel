const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function startScan(githubUrl?: string, liveUrl?: string) {
  const res = await fetch(`${API_URL}/api/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_url: githubUrl, live_url: liveUrl }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function uploadZip(file: File) {
  const form = new FormData()
  form.append("file", file)
  const res = await fetch(`${API_URL}/api/scan/upload`, { method: "POST", body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getScan(scanId: string) {
  const res = await fetch(`${API_URL}/api/scan/${scanId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getReport(scanId: string) {
  const res = await fetch(`${API_URL}/api/report/${scanId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function listScans() {
  const res = await fetch(`${API_URL}/api/scan/`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function createPR(scanId: string, githubToken: string, repoUrl: string) {
  const res = await fetch(`${API_URL}/api/github/pr`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scan_id: scanId, github_token: githubToken, repo_url: repoUrl }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function getBadgeUrl(scanId: string) {
  return `${API_URL}/api/report/${scanId}/badge`
}
