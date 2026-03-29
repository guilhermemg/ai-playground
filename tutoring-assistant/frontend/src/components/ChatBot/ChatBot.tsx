import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { createChatConnection, type ChatMessage } from '../../services/websocket'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  agentName?: string
}

export default function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const connRef = useRef<ReturnType<typeof createChatConnection> | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const currentResponseRef = useRef('')
  const currentAgentRef = useRef('')

  useEffect(() => {
    connect()
    return () => connRef.current?.close()
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const connect = () => {
    const conn = createChatConnection(
      (msg: ChatMessage) => {
        switch (msg.type) {
          case 'system':
            setConnected(true)
            setMessages(prev => [...prev, { role: 'system', content: msg.content || 'Connected' }])
            break
          case 'routing':
            currentAgentRef.current = msg.agent_name || ''
            currentResponseRef.current = ''
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: '',
              agentName: msg.agent_name,
            }])
            setStreaming(true)
            break
          case 'token':
            currentResponseRef.current += msg.content || ''
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last?.role === 'assistant') {
                updated[updated.length - 1] = { ...last, content: currentResponseRef.current }
              }
              return updated
            })
            break
          case 'done':
            setStreaming(false)
            break
          case 'error':
            setMessages(prev => [...prev, { role: 'system', content: `Error: ${msg.content}` }])
            setStreaming(false)
            break
        }
      },
      () => {
        setConnected(false)
        setMessages(prev => [...prev, { role: 'system', content: 'Disconnected' }])
      },
    )
    connRef.current = conn
  }

  const handleSend = () => {
    if (!input.trim() || !connected || streaming) return
    setMessages(prev => [...prev, { role: 'user', content: input }])
    connRef.current?.send(input)
    setInput('')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Chat</h2>

      <div ref={scrollRef} className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role !== 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <Bot size={16} className="text-blue-600" />
              </div>
            )}
            <div className={`max-w-[70%] ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2'
                : msg.role === 'system'
                ? 'bg-gray-100 text-gray-500 rounded-lg px-3 py-1.5 text-sm italic'
                : 'bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2'
            }`}>
              {msg.agentName && (
                <p className="text-xs font-medium text-blue-600 mb-1">{msg.agentName}</p>
              )}
              <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
              {msg.role === 'assistant' && streaming && i === messages.length - 1 && (
                <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-0.5" />
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                <User size={16} className="text-white" />
              </div>
            )}
          </div>
        ))}
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Start a conversation by typing a question below.</p>
          </div>
        )}
      </div>

      <div className="flex gap-2 mt-4">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder={connected ? 'Ask a question...' : 'Connecting...'}
          disabled={!connected}
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
        />
        <button
          onClick={handleSend}
          disabled={!connected || streaming || !input.trim()}
          className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}
