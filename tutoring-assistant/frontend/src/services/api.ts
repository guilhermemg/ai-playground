const BASE_URL = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(`${res.status}: ${error}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// Agents
export interface Agent {
  id: string
  name: string
  domain: string
  description: string
  is_active: boolean
  enabled_tools: string[]
  active_prompt_version_id: string | null
  created_at: string
  updated_at: string
}

export interface PromptVersion {
  id: string
  agent_id: string
  version: number
  system_message: string
  full_prompt: string
  created_at: string
}

export interface ToolDef {
  name: string
  description: string
}

export const agentsApi = {
  list: () => request<Agent[]>('/agents'),
  get: (id: string) => request<Agent>(`/agents/${id}`),
  create: (data: { name: string; domain: string; description?: string; enabled_tools?: string[]; additional_instructions?: string }) =>
    request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Agent>) =>
    request<Agent>(`/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/agents/${id}`, { method: 'DELETE' }),
  getPrompt: (id: string) => request<PromptVersion>(`/agents/${id}/prompt`),
  updatePrompt: (id: string, data: { system_message: string; full_prompt: string }) =>
    request<PromptVersion>(`/agents/${id}/prompt`, { method: 'PUT', body: JSON.stringify(data) }),
  listPromptVersions: (id: string) => request<PromptVersion[]>(`/agents/${id}/prompt/versions`),
  activateVersion: (agentId: string, versionId: string) =>
    request<void>(`/agents/${agentId}/prompt/versions/${versionId}/activate`, { method: 'PUT' }),
  getTools: () => request<ToolDef[]>('/agents/tools'),
}

// Questionnaires
export interface QuestionItem {
  question: string
  answer: string
}

export interface Questionnaire {
  id: string
  title: string
  content: string
  status: string
  created_at: string
  updated_at: string
}

export interface QuestionnaireResult {
  id: string
  question_text: string
  answer_text: string
  agent_domain: string
  feedback: string
  score: number | null
  is_correct: boolean | null
  correct_answer: string | null
}

export interface QuestionnaireDetail {
  id: string
  title: string
  status: string
  created_at: string
  results: QuestionnaireResult[]
}

export interface EvalStreamEvent {
  type: 'start' | 'result' | 'done' | 'error'
  total?: number
  completed?: number
  elapsed?: number
  message?: string
  result?: {
    id: string
    question_index: number
    question_text: string
    answer_text: string
    agent_domain: string
    feedback: string
    score: number | null
    is_correct: boolean | null
    correct_answer: string | null
  }
}

export const questionnairesApi = {
  list: () => request<Questionnaire[]>('/questionnaires'),
  get: (id: string) => request<QuestionnaireDetail>(`/questionnaires/${id}`),
  create: (data: { title: string; questions: QuestionItem[] }) =>
    request<Questionnaire>('/questionnaires', { method: 'POST', body: JSON.stringify(data) }),
  evaluate: (id: string) =>
    request<{ status: string }>(`/questionnaires/${id}/evaluate`, { method: 'POST' }),
  evaluateStream: (
    id: string,
    onEvent: (event: EvalStreamEvent) => void,
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      fetch(`${BASE_URL}/questionnaires/${id}/evaluate`, { method: 'POST' })
        .then(async (res) => {
          if (!res.ok) {
            const error = await res.text()
            reject(new Error(`${res.status}: ${error}`))
            return
          }
          const reader = res.body?.getReader()
          if (!reader) { reject(new Error('No response body')); return }

          const decoder = new TextDecoder()
          let buffer = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })

            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              const trimmed = line.trim()
              if (trimmed.startsWith('data: ')) {
                try {
                  const event = JSON.parse(trimmed.slice(6)) as EvalStreamEvent
                  onEvent(event)
                } catch { /* skip malformed */ }
              }
            }
          }
          resolve()
        })
        .catch(reject)
    })
  },
}

// Documents
export interface Document {
  id: string
  filename: string
  file_type: string
  assigned_agent_id: string | null
  chunk_count: number
  created_at: string
}

export const documentsApi = {
  list: () => request<Document[]>('/documents'),
  upload: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE_URL}/documents`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
    return res.json() as Promise<Document>
  },
  delete: (id: string) => request<void>(`/documents/${id}`, { method: 'DELETE' }),
  assign: (docId: string, agentId: string) =>
    request<Document>(`/documents/${docId}/assign/${agentId}`, { method: 'POST' }),
}

// Evaluation
export interface EvalRun {
  id: string
  status: string
  dataset_domain: string | null
  results: Record<string, unknown> | null
  triggered_at: string
  completed_at: string | null
}

export const evaluationApi = {
  run: (domain?: string) =>
    request<EvalRun>('/evaluation/run', { method: 'POST', body: JSON.stringify({ domain: domain || null }) }),
  listResults: () => request<EvalRun[]>('/evaluation/results'),
  getResult: (id: string) => request<EvalRun>(`/evaluation/results/${id}`),
}

// Config
export interface ObservabilityLinks {
  jaeger_url: string
  grafana_url: string
  langsmith_url: string
}

export const configApi = {
  getObservabilityLinks: () => request<ObservabilityLinks>('/config/observability'),
}
