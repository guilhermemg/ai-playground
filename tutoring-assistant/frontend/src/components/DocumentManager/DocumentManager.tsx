import { useEffect, useState, useCallback } from 'react'
import { Upload, Trash2, FileText } from 'lucide-react'
import { documentsApi, agentsApi } from '../../services/api'
import type { Document, Agent } from '../../services/api'

export default function DocumentManager() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = () => {
    documentsApi.list().then(setDocuments).catch(console.error)
    agentsApi.list().then(setAgents).catch(console.error)
  }

  const handleUpload = async (files: FileList | File[]) => {
    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        await documentsApi.upload(file)
      }
      loadData()
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files)
  }, [])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this document?')) return
    await documentsApi.delete(id)
    loadData()
  }

  const handleAssign = async (docId: string, agentId: string) => {
    if (!agentId) return
    await documentsApi.assign(docId, agentId)
    loadData()
  }

  const getAgentName = (agentId: string | null) => {
    if (!agentId) return 'Unassigned'
    return agents.find(a => a.id === agentId)?.name || 'Unknown'
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Documents</h2>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center mb-6 transition-colors ${
          dragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 bg-white'
        }`}
      >
        <Upload size={40} className="mx-auto text-gray-400 mb-3" />
        <p className="text-gray-600 mb-2">Drag and drop files here</p>
        <p className="text-sm text-gray-400 mb-4">Supports PDF, DOCX, TXT, MD</p>
        <label className="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
          {uploading ? 'Uploading...' : 'Browse Files'}
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt,.md"
            onChange={e => e.target.files && handleUpload(e.target.files)}
            className="hidden"
          />
        </label>
      </div>

      {/* Document table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">File</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Chunks</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Assigned Agent</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {documents.map(doc => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-gray-400" />
                    <span className="text-sm font-medium text-gray-900">{doc.filename}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{doc.file_type}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{doc.chunk_count}</td>
                <td className="px-6 py-4">
                  <select
                    value={doc.assigned_agent_id || ''}
                    onChange={e => handleAssign(doc.id, e.target.value)}
                    className="text-sm border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="">Unassigned</option>
                    {agents.map(a => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(doc.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-red-500 hover:text-red-700 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No documents uploaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
