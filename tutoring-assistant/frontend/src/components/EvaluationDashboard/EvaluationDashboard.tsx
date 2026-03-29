import { useEffect, useState } from 'react'
import { Play, Download, ChevronDown, ChevronUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { evaluationApi } from '../../services/api'
import type { EvalRun } from '../../services/api'

const METRIC_LABELS: Record<string, string> = {
  faithfulness: 'Faithfulness',
  answer_relevancy: 'Answer Relevancy',
  context_precision: 'Context Precision',
  context_recall: 'Context Recall',
  answer_correctness: 'Answer Correctness',
  routing_accuracy: 'Routing Accuracy',
}

const METRIC_COLORS: Record<string, string> = {
  faithfulness: '#3b82f6',
  answer_relevancy: '#10b981',
  context_precision: '#f59e0b',
  context_recall: '#8b5cf6',
  answer_correctness: '#ef4444',
  routing_accuracy: '#06b6d4',
}

export default function EvaluationDashboard() {
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [domain, setDomain] = useState('')
  const [running, setRunning] = useState(false)
  const [expandedRun, setExpandedRun] = useState<string | null>(null)

  useEffect(() => {
    loadRuns()
  }, [])

  const loadRuns = () => {
    evaluationApi.listResults().then(setRuns).catch(console.error)
  }

  const handleRun = async () => {
    setRunning(true)
    try {
      await evaluationApi.run(domain || undefined)
      setTimeout(loadRuns, 2000)
    } finally {
      setRunning(false)
    }
  }

  const latestCompleted = runs.find(r => r.status === 'completed' && r.results)
  const latestMetrics = (latestCompleted?.results as any)?.metrics || {}
  const latestPerQuestion = (latestCompleted?.results as any)?.per_question || []

  const chartData = runs
    .filter(r => r.status === 'completed' && r.results)
    .reverse()
    .map((r, i) => {
      const metrics = (r.results as any)?.metrics || {}
      return {
        run: `Run ${i + 1}`,
        ...Object.fromEntries(
          Object.keys(METRIC_LABELS).map(k => [k, metrics[k] != null ? Math.round(metrics[k] * 100) / 100 : null])
        ),
      }
    })

  const scoreColor = (v: number | null | undefined) => {
    if (v == null) return 'text-gray-400'
    if (v >= 0.7) return 'text-green-600'
    if (v >= 0.4) return 'text-yellow-600'
    return 'text-red-600'
  }

  const scoreBg = (v: number | null | undefined) => {
    if (v == null) return 'bg-gray-50'
    if (v >= 0.7) return 'bg-green-50'
    if (v >= 0.4) return 'bg-yellow-50'
    return 'bg-red-50'
  }

  const exportCsv = () => {
    if (!latestPerQuestion.length) return
    const header = 'Question,Answer,Ground Truth,Domain\n'
    const rows = latestPerQuestion.map((q: any) =>
      `"${q.question}","${q.answer}","${q.ground_truth}","${q.domain}"`
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'evaluation_results.csv'
    a.click()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Evaluation</h2>
        <div className="flex items-center gap-3">
          <select
            value={domain}
            onChange={e => setDomain(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All Domains</option>
            <option value="medicine">Medicine</option>
            <option value="physics">Physics</option>
            <option value="math">Math</option>
            <option value="law">Law</option>
            <option value="engineering">Engineering</option>
          </select>
          <button
            onClick={handleRun}
            disabled={running}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Play size={18} /> {running ? 'Running...' : 'Run Evaluation'}
          </button>
          {latestPerQuestion.length > 0 && (
            <button
              onClick={exportCsv}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Download size={16} /> Export CSV
            </button>
          )}
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {Object.entries(METRIC_LABELS).map(([key, label]) => (
          <div key={key} className={`rounded-xl border border-gray-200 p-4 ${scoreBg(latestMetrics[key])}`}>
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className={`text-2xl font-bold ${scoreColor(latestMetrics[key])}`}>
              {latestMetrics[key] != null ? (latestMetrics[key] * 100).toFixed(1) + '%' : 'N/A'}
            </p>
          </div>
        ))}
      </div>

      {/* Trend chart */}
      {chartData.length > 1 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Metric Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="run" />
              <YAxis domain={[0, 1]} />
              <Tooltip />
              <Legend />
              {Object.entries(METRIC_LABELS).map(([key, label]) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  name={label}
                  stroke={METRIC_COLORS[key]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Per-question results */}
      {latestPerQuestion.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Per-Question Results</h3>
          <div className="space-y-3">
            {latestPerQuestion.map((q: any, i: number) => (
              <div key={i} className="border border-gray-100 rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Q{i + 1}: {q.question.slice(0, 80)}...</span>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{q.domain}</span>
                </div>
                <p className="text-xs text-gray-600"><strong>Answer:</strong> {q.answer?.slice(0, 150)}</p>
                <p className="text-xs text-gray-500 mt-1"><strong>Ground Truth:</strong> {q.ground_truth?.slice(0, 150)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Run history */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Run History</h3>
        <div className="space-y-2">
          {runs.map(run => (
            <div key={run.id} className="border border-gray-200 rounded-lg">
              <div
                className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpandedRun(expandedRun === run.id ? null : run.id)}
              >
                <div className="flex items-center gap-3">
                  {expandedRun === run.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  <span className="text-sm">{new Date(run.triggered_at).toLocaleString()}</span>
                  {run.dataset_domain && (
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{run.dataset_domain}</span>
                  )}
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  run.status === 'completed' ? 'bg-green-100 text-green-700' :
                  run.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {run.status}
                </span>
              </div>
              {expandedRun === run.id && run.results && (
                <div className="border-t p-3 bg-gray-50">
                  <pre className="text-xs overflow-auto">{JSON.stringify(run.results, null, 2)}</pre>
                </div>
              )}
            </div>
          ))}
          {runs.length === 0 && (
            <p className="text-gray-500 text-center py-4">No evaluation runs yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
