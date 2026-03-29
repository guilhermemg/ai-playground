import { Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ClipboardList,
  Bot,
  FileText,
  MessageSquare,
  BarChart3,
} from 'lucide-react'
import Dashboard from './components/Dashboard/Dashboard'
import QuestionnaireManager from './components/QuestionnaireManager/QuestionnaireManager'
import AgentCreator from './components/AgentCreator/AgentCreator'
import AgentConfigPanel from './components/AgentConfigPanel/AgentConfigPanel'
import DocumentManager from './components/DocumentManager/DocumentManager'
import ChatBot from './components/ChatBot/ChatBot'
import EvaluationDashboard from './components/EvaluationDashboard/EvaluationDashboard'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/questionnaires', icon: ClipboardList, label: 'Questionnaires' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/evaluation', icon: BarChart3, label: 'Evaluation' },
]

export default function App() {
  return (
    <div className="flex h-screen bg-gray-50">
      <nav className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Tutoring Assistant</h1>
          <p className="text-sm text-gray-500 mt-1">Admin Panel</p>
        </div>
        <div className="flex-1 py-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-blue-600 bg-blue-50 border-r-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`
              }
            >
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/questionnaires" element={<QuestionnaireManager />} />
            <Route path="/agents" element={<AgentCreator />} />
            <Route path="/agents/:id" element={<AgentConfigPanel />} />
            <Route path="/documents" element={<DocumentManager />} />
            <Route path="/chat" element={<ChatBot />} />
            <Route path="/evaluation" element={<EvaluationDashboard />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
