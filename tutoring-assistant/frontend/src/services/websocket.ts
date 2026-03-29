export interface ChatMessage {
  type: 'system' | 'routing' | 'token' | 'done' | 'error'
  content?: string
  agent_name?: string
  domain?: string
  agents?: { id: string; name: string; domain: string }[]
}

export function createChatConnection(
  onMessage: (msg: ChatMessage) => void,
  onClose?: () => void,
): { send: (message: string) => void; close: () => void } {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat`)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as ChatMessage
      onMessage(msg)
    } catch {
      onMessage({ type: 'error', content: 'Failed to parse message' })
    }
  }

  ws.onclose = () => onClose?.()
  ws.onerror = () => onMessage({ type: 'error', content: 'WebSocket connection error' })

  return {
    send: (message: string) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ message }))
      }
    },
    close: () => ws.close(),
  }
}
