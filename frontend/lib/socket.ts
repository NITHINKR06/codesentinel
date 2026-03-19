import { ScanEvent } from "@/types"

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

export function connectToScan(
  scanId: string,
  onEvent: (event: ScanEvent) => void,
  onComplete: () => void,
  onError: (err: Event) => void
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/scan/${scanId}`)

  ws.onmessage = (msg) => {
    try {
      const event: ScanEvent = JSON.parse(msg.data)
      onEvent(event)
      if (event.stage === "complete" || event.stage === "failed") {
        onComplete()
        ws.close()
      }
    } catch {
      // ignore parse errors
    }
  }

  ws.onerror = onError
  ws.onclose = () => {}

  return ws
}
