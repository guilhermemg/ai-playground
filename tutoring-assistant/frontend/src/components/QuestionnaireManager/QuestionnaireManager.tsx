import { useEffect, useState, useCallback } from 'react'
import { Plus, Play, RefreshCw, ChevronDown, ChevronUp, CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { questionnairesApi } from '../../services/api'
import type { Questionnaire, QuestionnaireDetail, QuestionItem, QuestionnaireResult, EvalStreamEvent } from '../../services/api'

function OverallGrade({ results, total }: { results: QuestionnaireResult[]; total: number }) {
  const graded = results.filter(r => r.is_correct !== null && r.is_correct !== undefined)
  if (graded.length === 0) return null

  const correctCount = graded.filter(r => r.is_correct).length
  const pct = Math.round((correctCount / total) * 100)
  const allDone = results.length === total
  const color = pct >= 70 ? 'text-green-600 bg-green-50 border-green-200'
    : pct >= 40 ? 'text-yellow-600 bg-yellow-50 border-yellow-200'
    : 'text-red-600 bg-red-50 border-red-200'
  const icon = pct >= 70 ? <CheckCircle2 size={28} /> : pct >= 40 ? <AlertCircle size={28} /> : <XCircle size={28} />

  return (
    <div className={`flex items-center justify-between rounded-xl border-2 p-5 mb-5 ${color}`}>
      <div className="flex items-center gap-3">
        {icon}
        <div>
          <p className="text-lg font-bold">{allDone ? 'Exam Score' : 'Score (in progress...)'}</p>
          <p className="text-sm opacity-75">{correctCount} of {total} correct ({graded.length} graded)</p>
        </div>
      </div>
      <p className="text-4xl font-extrabold">{pct}%</p>
    </div>
  )
}

function ResultCard({ result, index, isNew }: { result: QuestionnaireResult; index: number; isNew?: boolean }) {
  const isCorrect = result.is_correct
  const verdictBadge = isCorrect === true
    ? 'bg-green-100 text-green-700 border-green-300'
    : isCorrect === false
    ? 'bg-red-100 text-red-700 border-red-300'
    : 'bg-gray-100 text-gray-600 border-gray-300'
  const verdictIcon = isCorrect === true
    ? <CheckCircle2 size={16} className="text-green-600" />
    : isCorrect === false
    ? <XCircle size={16} className="text-red-600" />
    : <AlertCircle size={16} className="text-gray-500" />
  const verdictLabel = isCorrect === true ? 'Correct' : isCorrect === false ? 'Incorrect' : 'Unknown'

  return (
    <div className={`border border-gray-200 rounded-xl p-5 bg-white transition-all duration-500 ${isNew ? 'animate-fadeIn ring-2 ring-blue-300 ring-opacity-50' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <p className="font-semibold text-gray-900">Question {index + 1}</p>
        <div className="flex items-center gap-2">
          <span className="text-xs bg-blue-100 text-blue-700 px-2.5 py-1 rounded-full font-medium">
            {result.agent_domain}
          </span>
          <span className={`flex items-center gap-1 text-sm font-bold px-2.5 py-1 rounded-full border ${verdictBadge}`}>
            {verdictIcon} {verdictLabel}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Question</p>
          <p className="text-sm text-gray-800">{result.question_text}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Student Answer</p>
          <p className="text-sm text-gray-800">{result.answer_text}</p>
        </div>
      </div>

      {result.correct_answer && isCorrect === false && (
        <div className="bg-green-50 rounded-lg p-3 mb-3 border border-green-200">
          <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-1">Correct Answer</p>
          <p className="text-sm text-green-800 font-medium">{result.correct_answer}</p>
        </div>
      )}

      <div className="bg-blue-50 rounded-lg p-4">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Feedback</p>
        <div className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
          {result.feedback}
        </div>
      </div>
    </div>
  )
}

function PendingQuestionSlot({ index }: { index: number }) {
  return (
    <div className="border border-gray-200 border-dashed rounded-xl p-5 bg-gray-50 flex items-center gap-3">
      <Loader2 size={18} className="animate-spin text-blue-500" />
      <p className="text-sm text-gray-500 font-medium">Question {index + 1} — evaluating...</p>
    </div>
  )
}

export default function QuestionnaireManager() {
  const [questionnaires, setQuestionnaires] = useState<Questionnaire[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<QuestionnaireDetail | null>(null)
  const [title, setTitle] = useState('')
  const [questionsText, setQuestionsText] = useState('')

  const [streamingId, setStreamingId] = useState<string | null>(null)
  const [streamResults, setStreamResults] = useState<Map<number, QuestionnaireResult>>(new Map())
  const [streamTotal, setStreamTotal] = useState(0)
  const [lastAddedIndex, setLastAddedIndex] = useState<number | null>(null)

  useEffect(() => {
    loadQuestionnaires()
  }, [])

  const loadQuestionnaires = () => {
    questionnairesApi.list().then(setQuestionnaires).catch(console.error)
  }

  const handleCreate = async () => {
    const lines = questionsText.trim().split('\n')
    const questions: QuestionItem[] = []
    for (let i = 0; i < lines.length; i += 2) {
      const q = lines[i]?.replace(/^Q:\s*/i, '').trim()
      const a = lines[i + 1]?.replace(/^A:\s*/i, '').trim()
      if (q && a) questions.push({ question: q, answer: a })
    }
    if (!title || questions.length === 0) return

    await questionnairesApi.create({ title, questions })
    setTitle('')
    setQuestionsText('')
    setShowCreate(false)
    loadQuestionnaires()
  }

  const handleEvaluate = useCallback(async (id: string) => {
    setStreamingId(id)
    setStreamResults(new Map())
    setStreamTotal(0)
    setLastAddedIndex(null)
    setExpandedId(id)
    setDetail(null)

    setQuestionnaires(prev => prev.map(q =>
      q.id === id ? { ...q, status: 'evaluating' } : q
    ))

    try {
      await questionnairesApi.evaluateStream(id, (event: EvalStreamEvent) => {
        if (event.type === 'start') {
          setStreamTotal(event.total ?? 0)
        } else if (event.type === 'result' && event.result) {
          const r = event.result
          const result: QuestionnaireResult = {
            id: r.id,
            question_text: r.question_text,
            answer_text: r.answer_text,
            agent_domain: r.agent_domain,
            feedback: r.feedback,
            score: r.score,
            is_correct: r.is_correct ?? null,
            correct_answer: r.correct_answer ?? null,
          }
          setStreamResults(prev => {
            const next = new Map(prev)
            next.set(r.question_index, result)
            return next
          })
          setLastAddedIndex(r.question_index)
          setTimeout(() => setLastAddedIndex(null), 1500)
        } else if (event.type === 'done') {
          setStreamingId(null)
          loadQuestionnaires()
          questionnairesApi.get(id).then(setDetail).catch(console.error)
        } else if (event.type === 'error') {
          setStreamingId(null)
          loadQuestionnaires()
        }
      })
    } catch {
      setStreamingId(null)
      loadQuestionnaires()
    }
  }, [])

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null)
      setDetail(null)
      return
    }
    const d = await questionnairesApi.get(id)
    setDetail(d)
    setExpandedId(id)
  }

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      evaluating: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100'}`}>
        {status}
      </span>
    )
  }

  const renderStreamingResults = (q: Questionnaire) => {
    let parsedQuestions: { question: string; answer: string }[] = []
    try { parsedQuestions = JSON.parse(q.content) } catch {}
    const total = streamTotal || parsedQuestions.length

    const resultsArray = Array.from(streamResults.values())

    return (
      <div>
        {resultsArray.length > 0 && (
          <OverallGrade results={resultsArray} total={total} />
        )}

        <div className="flex items-center gap-2 mb-4">
          <Loader2 size={16} className="animate-spin text-blue-500" />
          <p className="text-sm text-blue-600 font-medium">
            Evaluating in parallel — {streamResults.size} of {total} completed
          </p>
        </div>

        <div className="space-y-4">
          {Array.from({ length: total }, (_, i) => {
            const result = streamResults.get(i)
            if (result) {
              return <ResultCard key={`result-${i}`} result={result} index={i} isNew={lastAddedIndex === i} />
            }
            return <PendingQuestionSlot key={`pending-${i}`} index={i} />
          })}
        </div>
      </div>
    )
  }

  return (
    <div>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.4s ease-out; }
      `}</style>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Questionnaires</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} /> New Questionnaire
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Create Questionnaire</h3>
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={e => setTitle(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 mb-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <textarea
            placeholder={"Enter questions and answers, alternating lines:\nQ: What is gravity?\nA: A fundamental force of attraction\nQ: What is F=ma?\nA: Newton's second law"}
            value={questionsText}
            onChange={e => setQuestionsText(e.target.value)}
            rows={10}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 mb-4 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Submit
          </button>
        </div>
      )}

      <div className="space-y-4">
        {questionnaires.map(q => (
          <div key={q.id} className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-4 cursor-pointer" onClick={() => handleExpand(q.id)}>
                {expandedId === q.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                <div>
                  <p className="font-medium text-gray-900">{q.title}</p>
                  <p className="text-sm text-gray-500">{new Date(q.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {statusBadge(streamingId === q.id ? 'evaluating' : q.status)}
                {streamingId !== q.id && q.status !== 'evaluating' && (
                  <button
                    onClick={() => handleEvaluate(q.id)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors"
                  >
                    {q.status === 'pending' ? <Play size={16} /> : <RefreshCw size={16} />}
                    {q.status === 'pending' ? 'Evaluate' : 'Re-evaluate'}
                  </button>
                )}
                {(streamingId === q.id || q.status === 'evaluating') && (
                  <span className="flex items-center gap-1 px-3 py-1.5 text-blue-600 text-sm">
                    <RefreshCw size={16} className="animate-spin" /> Evaluating...
                  </span>
                )}
              </div>
            </div>

            {expandedId === q.id && (
              <div className="border-t border-gray-200 p-5">
                {streamingId === q.id ? renderStreamingResults(q) : (() => {
                  let parsedQuestions: { question: string; answer: string }[] = []
                  try { parsedQuestions = JSON.parse(q.content) } catch {}

                  if (detail && detail.results.length > 0) {
                    return (
                      <div>
                        <OverallGrade results={detail.results} total={detail.results.length} />
                        <div className="space-y-4">
                          {detail.results.map((r, i) => (
                            <ResultCard key={r.id} result={r} index={i} />
                          ))}
                        </div>
                      </div>
                    )
                  }

                  if (parsedQuestions.length > 0) {
                    return (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-3">Questions & Student Answers</h4>
                        <div className="space-y-3">
                          {parsedQuestions.map((item, i) => (
                            <div key={i} className="border border-gray-100 rounded-lg p-4 bg-gray-50">
                              <p className="font-medium text-gray-900 mb-1">Question {i + 1}</p>
                              <p className="text-sm text-gray-700 mb-1"><strong>Q:</strong> {item.question}</p>
                              <p className="text-sm text-gray-700"><strong>A:</strong> {item.answer}</p>
                            </div>
                          ))}
                        </div>
                        {q.status === 'pending' && (
                          <p className="text-gray-500 text-sm mt-4">Click "Evaluate" to check which answers are correct.</p>
                        )}
                      </div>
                    )
                  }

                  return <p className="text-gray-500 text-sm">No content available.</p>
                })()}
              </div>
            )}
          </div>
        ))}
        {questionnaires.length === 0 && (
          <p className="text-gray-500 text-center py-8">No questionnaires yet. Create one to get started.</p>
        )}
      </div>
    </div>
  )
}
