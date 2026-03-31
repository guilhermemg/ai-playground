import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Save, History } from 'lucide-react'
import { agentsApi, documentsApi } from '../../services/api'
import type { Agent, PromptVersion, ToolDef, Document } from '../../services/api'

export default function AgentConfigPanel() {
  const { id } = useParams<{ id: string }>()
  const [agent, setAgent] = useState<Agent | null>(null)
  const [prompt, setPrompt] = useState<PromptVersion | null>(null)
  const [versions, setVersions] = useState<PromptVersion[]>([])
  const [availableTools, setAvailableTools] = useState<ToolDef[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [systemMessage, setSystemMessage] = useState('')
  const [fullPrompt, setFullPrompt] = useState('')
  const [enabledTools, setEnabledTools] = useState<string[]>([])
  const [showVersions, setShowVersions] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) return
    loadAgent()
    agentsApi.getTools().then(setAvailableTools).catch(console.error)
    documentsApi.list().then(setDocuments).catch(console.error)
  }, [id])

  const loadAgent = async () => {
    if (!id) return
    const a = await agentsApi.get(id)
    setAgent(a)
    setEnabledTools(a.enabled_tools)

    const p = await agentsApi.getPrompt(id)
    setPrompt(p)
    setSystemMessage(p.system_message)
    setFullPrompt(p.full_prompt)

    const v = await agentsApi.listPromptVersions(id)
    setVersions(v)
  }

  const handleToggleTool = async (toolName: string) => {
    if (!id) return
    const updated = enabledTools.includes(toolName)
      ? enabledTools.filter(t => t !== toolName)
      : [...enabledTools, toolName]
    setEnabledTools(updated)
    await agentsApi.update(id, { enabled_tools: updated })
  }

  const handleSavePrompt = async () => {
    if (!id) return
    setSaving(true)
    try {
      const p = await agentsApi.updatePrompt(id, { system_message: systemMessage, full_prompt: fullPrompt })
      setPrompt(p)
      const v = await agentsApi.listPromptVersions(id)
      setVersions(v)
    } finally {
      setSaving(false)
    }
  }

  const handleActivateVersion = async (versionId: string) => {
    if (!id) return
    await agentsApi.activateVersion(id, versionId)
    await loadAgent()
  }

  const handleAssignDoc = async (docId: string) => {
    if (!id) return
    await documentsApi.assign(docId, id)
    documentsApi.list().then(setDocuments).catch(console.error)
  }

  const agentDocs = documents.filter(d => d.assigned_agent_id === id)
  const unassignedDocs = documents.filter(d => !d.assigned_agent_id)

  if (!agent) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{agent.name}</h2>
        <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">{agent.domain}</span>
        <span className={`px-3 py-1 rounded-full text-sm ${agent.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {agent.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      {/* Tools */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 mb-4">Tools</h3>
        <div className="grid grid-cols-2 gap-3">
          {availableTools.map(tool => (
            <label key={tool.name} className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
              <input
                type="checkbox"
                checked={enabledTools.includes(tool.name)}
                onChange={() => handleToggleTool(tool.name)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <div>
                <p className="font-medium text-gray-900 text-sm">{tool.name}</p>
                <p className="text-xs text-gray-500">{tool.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Prompt Editor */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Prompt (v{prompt?.version})</h3>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowVersions(!showVersions)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <History size={16} /> Version History
            </button>
            <button
              onClick={handleSavePrompt}
              disabled={saving}
              className="flex items-center gap-1 px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Save size={16} /> {saving ? 'Saving...' : 'Save New Version'}
            </button>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">System Message</label>
          <textarea
            value={systemMessage}
            onChange={e => setSystemMessage(e.target.value)}
            rows={8}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Prompt Template</label>
          <textarea
            value={fullPrompt}
            onChange={e => setFullPrompt(e.target.value)}
            rows={10}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {showVersions && (
          <div className="mt-4 border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Version History</h4>
            <div className="space-y-2 max-h-60 overflow-auto">
              {versions.map(v => (
                <div key={v.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <div>
                    <span className="font-medium text-sm">v{v.version}</span>
                    <span className="text-xs text-gray-500 ml-2">{new Date(v.created_at).toLocaleString()}</span>
                  </div>
                  <button
                    onClick={() => {
                      setSystemMessage(v.system_message)
                      setFullPrompt(v.full_prompt)
                      handleActivateVersion(v.id)
                    }}
                    className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                      prompt?.id === v.id
                        ? 'bg-green-100 text-green-700'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-blue-50'
                    }`}
                  >
                    {prompt?.id === v.id ? 'Active' : 'Activate'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Documents */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Assigned Documents</h3>
        {agentDocs.length > 0 ? (
          <div className="space-y-2 mb-4">
            {agentDocs.map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div>
                  <p className="text-sm font-medium">{doc.filename}</p>
                  <p className="text-xs text-gray-500">{doc.chunk_count} chunks</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 mb-4">No documents assigned.</p>
        )}
        {unassignedDocs.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Assign a document</label>
            <select
              onChange={e => e.target.value && handleAssignDoc(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 text-sm"
              defaultValue=""
            >
              <option value="">Select document...</option>
              {unassignedDocs.map(d => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  )
}
