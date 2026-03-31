import { useEffect, useState } from 'react'
import { ClipboardList, Bot, FileText, ExternalLink } from 'lucide-react'
import { agentsApi, questionnairesApi, documentsApi, configApi } from '../../services/api'
import type { ObservabilityLinks } from '../../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState({ questionnaires: 0, agents: 0, activeAgents: 0, documents: 0 })
  const [links, setLinks] = useState<ObservabilityLinks | null>(null)

  useEffect(() => {
    Promise.all([
      questionnairesApi.list(),
      agentsApi.list(),
      documentsApi.list(),
      configApi.getObservabilityLinks(),
    ]).then(([quests, agents, docs, obsLinks]) => {
      setStats({
        questionnaires: quests.length,
        agents: agents.length,
        activeAgents: agents.filter(a => a.is_active).length,
        documents: docs.length,
      })
      setLinks(obsLinks)
    }).catch(console.error)
  }, [])

  const cards = [
    { label: 'Questionnaires', value: stats.questionnaires, icon: ClipboardList, color: 'bg-blue-500' },
    { label: 'Active Agents', value: `${stats.activeAgents}/${stats.agents}`, icon: Bot, color: 'bg-green-500' },
    { label: 'Documents', value: stats.documents, icon: FileText, color: 'bg-purple-500' },
  ]

  const quickLinks = links ? [
    { label: 'Jaeger', url: links.jaeger_url, desc: 'Distributed traces' },
    { label: 'Grafana', url: links.grafana_url, desc: 'Metrics dashboards' },
    { label: 'LangSmith', url: links.langsmith_url, desc: 'LLM traces & reasoning' },
  ] : []

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
              </div>
              <div className={`${color} p-3 rounded-lg`}>
                <Icon size={24} className="text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {quickLinks.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Observability Quick Links</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quickLinks.map(({ label, url, desc }) => (
              <a
                key={label}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <ExternalLink size={20} className="text-blue-500 flex-shrink-0" />
                <div>
                  <p className="font-medium text-gray-900">{label}</p>
                  <p className="text-sm text-gray-500">{desc}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
