import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Power, Trash2, Settings } from 'lucide-react'
import { agentsApi } from '../../services/api'
import type { Agent } from '../../services/api'

export default function AgentCreator() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [domain, setDomain] = useState('')
  const [description, setDescription] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = () => {
    agentsApi.list().then(setAgents).catch(console.error)
  }

  const handleCreate = async () => {
    if (!name || !domain) return
    const agent = await agentsApi.create({ name, domain, description })
    setName('')
    setDomain('')
    setDescription('')
    setShowCreate(false)
    loadAgents()
    navigate(`/agents/${agent.id}`)
  }

  const handleToggle = async (agent: Agent) => {
    await agentsApi.update(agent.id, { is_active: !agent.is_active })
    loadAgents()
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this agent? This action cannot be undone.')) return
    await agentsApi.delete(id)
    loadAgents()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Expert Agents</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} /> New Agent
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Create Expert Agent</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <input
              type="text"
              placeholder="Agent Name (e.g., Medicine Expert)"
              value={name}
              onChange={e => setName(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="text"
              placeholder="Domain (e.g., Medicine)"
              value={domain}
              onChange={e => setDomain(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <textarea
            placeholder="Description (optional)"
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={2}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 mb-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Agent
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map(agent => (
          <div key={agent.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                <span className="text-sm bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{agent.domain}</span>
              </div>
              <button
                onClick={() => handleToggle(agent)}
                className={`p-2 rounded-lg transition-colors ${
                  agent.is_active ? 'bg-green-100 text-green-600 hover:bg-green-200' : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                }`}
                title={agent.is_active ? 'Active - click to disable' : 'Inactive - click to enable'}
              >
                <Power size={18} />
              </button>
            </div>
            {agent.description && <p className="text-sm text-gray-600 mb-3">{agent.description}</p>}
            <div className="flex flex-wrap gap-1 mb-3">
              {agent.enabled_tools.map(t => (
                <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{t}</span>
              ))}
              {agent.enabled_tools.length === 0 && <span className="text-xs text-gray-400">No tools</span>}
            </div>
            <div className="flex items-center gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => navigate(`/agents/${agent.id}`)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <Settings size={14} /> Configure
              </button>
              <button
                onClick={() => handleDelete(agent.id)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors ml-auto"
              >
                <Trash2 size={14} /> Delete
              </button>
            </div>
          </div>
        ))}
        {agents.length === 0 && (
          <p className="text-gray-500 col-span-full text-center py-8">No agents yet. Create one to get started.</p>
        )}
      </div>
    </div>
  )
}
