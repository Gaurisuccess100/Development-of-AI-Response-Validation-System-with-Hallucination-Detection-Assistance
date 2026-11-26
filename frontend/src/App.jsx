
import { useEffect, useMemo, useState } from 'react'
import { Routes, Route } from 'react-router-dom'

import { api, useAuth } from './context/AuthContext'
import AgentAnalysis from './AgentAnalysis'
import Login from './pages/Login'
import Register from './pages/Register'
import ProtectedRoute from './components/ProtectedRoute'

import {
  Activity, LayoutDashboard, FlaskConical, Bot, Database,
  History, ChartNoAxesCombined, Settings, Bell, Search,
  ChevronDown, ArrowUpRight, ShieldAlert, CheckCircle2,
  FileText, Menu, Plus, Sparkles, CircleHelp,
  LoaderCircle, Upload, Play, RefreshCw
} from 'lucide-react'

import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid, BarChart, Bar
} from 'recharts'

import './index.css'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const navigation = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Evaluation Studio', icon: FlaskConical },
  { label: 'Agent Analysis', icon: Bot },
  { label: 'Knowledge Hub', icon: Database },
  { label: 'History', icon: History },
  { label: 'Analytics', icon: ChartNoAxesCombined },
  { label: 'Settings', icon: Settings },
]

const agentDefinitions = [
  {
    key: 'relevance',
    name: 'Relevance Judge',
    detail: 'Checks whether the answer addresses the question.',
    icon: Search,
    color: 'purple',
  },
  {
    key: 'accuracy',
    name: 'Accuracy Judge',
    detail: 'Checks factual correctness against retrieved evidence.',
    icon: CheckCircle2,
    color: 'blue',
  },
  {
    key: 'hallucination',
    name: 'Hallucination Detector',
    detail: 'Identifies unsupported or fabricated claims.',
    icon: ShieldAlert,
    color: 'red',
  },
  {
    key: 'completeness',
    name: 'Completeness Judge',
    detail: 'Checks missing information and answer coverage.',
    icon: FileText,
    color: 'green',
  },
  {
    key: 'verdict',
    name: 'Verdict Agent',
    detail: 'Combines the findings into a final verdict.',
    icon: Sparkles,
    color: 'orange',
  },
]

function getScore(result) {
  if (!result) return null
  return result.score ?? result.overall_score ?? null
}

function formatScore(score) {
  if (score === null || score === undefined || !Number.isFinite(Number(score))) {
    return 'N/A'
  }

  return `${score}/10`
}

function getVerdictClass(verdict = '') {
  const value = String(verdict).toLowerCase()

  if (
    value.includes('fail') ||
    value.includes('incorrect') ||
    value.includes('not relevant') ||
    value.includes('hallucination detected') ||
    value.includes('incomplete')
  ) return 'danger'

  if (
    value.includes('improvement') ||
    value.includes('partial') ||
    value.includes('insufficient')
  ) return 'warning'

  if (
    value.includes('pass') ||
    value.includes('correct') ||
    value.includes('relevant') ||
    value.includes('complete') ||
    value.includes('no hallucination') ||
    value.includes('excellent') ||
    value.includes('good')
  ) return 'success'

  return 'neutral'
}

// NORMALIZE EVALUATION DATA

function normalizeEvaluation(item) {
  let report = {}

  try {
    if (typeof item.report === 'string') {
      report = JSON.parse(item.report)
    } else if (item.report && typeof item.report === 'object') {
      report = item.report
    } else if (item.report_json) {
      report = typeof item.report_json === 'string'
        ? JSON.parse(item.report_json)
        : item.report_json
    } else {
      // A fresh /api/evaluate response is itself the report.
      report = item
    }
  } catch (error) {
    console.error('Could not parse evaluation report:', error)
    report = item
  }

  const agents = report.agents || item.agents || {}

  const finalVerdict =
    report.final_verdict ||
    item.final_verdict ||
    agents.verdict ||
    {
      overall_score:
        item.overall_score ?? report.overall_score ?? null,
      final_verdict:
        item.verdict || report.verdict || 'Unknown',
    }

  const createdAt = item.created_at || report.created_at

  return {
    ...report,
    ...item,
    id: item.id ?? item.evaluation_id ?? Date.now().toString(),
    question: item.question || report.question || '',
    answer: item.answer || report.answer || '',
    agents,
    evidence: report.evidence || item.evidence || {},
    final_verdict: finalVerdict,
    createdAt: createdAt
      ? new Date(createdAt).toLocaleString()
      : item.createdAt || new Date().toLocaleString(),
  }
}

// TOOLTIP

function EvaluationTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  const item = payload[0].payload

  return (
    <div className="custom-tooltip">
      <strong>{label}</strong>
      <p>Overall score: {item.score}/10</p>
      {item.question && <p>{item.question}</p>}
      {item.date && <small>{item.date}</small>}
    </div>
  )
}

// SIDEBAR

function Sidebar({ active, setActive, open, setOpen }) {
  const { user, logout } = useAuth()

  return (
    <>
      {open && (
        <div
          className="mobile-overlay"
          onClick={() => setOpen(false)}
        />
      )}

      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-icon">
            <Sparkles size={22} />
          </div>

          <div>
            <div className="brand-name">
              AI Response <span>Validator</span>
            </div>
            <div className="brand-caption">
              INTELLIGENT VALIDATION PLATFORM
            </div>
          </div>
        </div>

        <div className="nav-caption">WORKSPACE</div>

        <nav className="nav-list">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${active === label ? 'active' : ''}`}
              onClick={() => {
                setActive(label)
                setOpen(false)
              }}
            >
              <Icon size={18} />
              <span>{label}</span>

              {label === 'Evaluation Studio' && (
                <span className="nav-new">LIVE</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="help-card">
            <CircleHelp size={19} className="help-icon" />

            <strong>Need some help?</strong>

            <p>
              Run an evaluation to validate an AI-generated response.
            </p>

            <button
              onClick={() => {
                setActive('Evaluation Studio')
                setOpen(false)
              }}
            >
              Start evaluation <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="user-profile">
            <div className="avatar">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>

            <div className="user-info">
              <strong>{user?.name || 'User'}</strong>
              <span>{user?.email || 'Logged in user'}</span>
            </div>

            <button
              className="icon-button"
              title="Logout"
              onClick={logout}
            >
              <ChevronDown size={16} />
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}

// STAT CARD

function StatCard({ icon: Icon, label, value, suffix, color, note }) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <div className={`stat-icon ${color}`}>
          <Icon size={18} />
        </div>
      </div>

      <div className="stat-value">
        {value}<small>{suffix}</small>
      </div>

      <div className="stat-change neutral-text">{note}</div>
    </div>
  )
}

// EMPTY STATE

function EmptyState({ text }) {
  return (
    <div className="empty-state">
      <FileText size={22} />
      <p>{text}</p>
    </div>
  )
}

// EVALUATION TABLE

function EvaluationTable({ evaluations }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Question</th>
            <th>Score</th>
            <th>Final verdict</th>
          </tr>
        </thead>

        <tbody>
          {evaluations.map(item => (
            <tr key={item.id}>
              <td className="question-cell">{item.question}</td>

              <td className="score-cell">
                {formatScore(item.final_verdict?.overall_score)}
              </td>

              <td>
                <span
                  className={`result-pill ${getVerdictClass(
                    item.final_verdict?.final_verdict
                  )}`}
                >
                  {item.final_verdict?.final_verdict || 'Unknown'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// DASHBOARD

function Dashboard({ evaluations, apiStatus, setActive }) {
  const scoredEvaluations = evaluations.filter(item =>
    Number.isFinite(Number(item.final_verdict?.overall_score))
    && item.final_verdict?.overall_score !== null
    && item.final_verdict?.overall_score !== undefined
  )

  const completed = evaluations.length

  const average = scoredEvaluations.length
    ? (
        scoredEvaluations.reduce(
          (sum, item) =>
            sum + Number(item.final_verdict.overall_score),
          0
        ) / scoredEvaluations.length
      ).toFixed(1)
    : '—'

  const hallucinations = evaluations.filter(
    item =>
      item.agents?.hallucination?.hallucination_detected === true
  ).length

  // Every evaluation has its own point on the graph.
  // Reverse the newest-first history to show oldest first.
  const chartData = [...scoredEvaluations]
    .reverse()
    .map((item, index) => ({
      name: `Evaluation ${index + 1}`,
      score: Number(item.final_verdict.overall_score),
      question: item.question,
      date: item.createdAt,
    }))

  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">
            <span className="live-dot" /> YOUR WORKSPACE
          </div>

          <h1>
            AI Response Validation <span className="wave">✦</span>
          </h1>

          <p className="page-description">
            Monitor, evaluate and validate AI-generated responses.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => setActive('Evaluation Studio')}
        >
          <Plus size={17} /> New evaluation
        </button>
      </div>

      <div className="connection-banner">
        <span
          className={`connection-dot ${
            apiStatus ? 'connected' : 'disconnected'
          }`}
        />

        Backend API: {apiStatus ? 'Connected' : 'Not connected'}

        <span className="connection-url">{API_BASE}</span>
      </div>

      <section className="stats-grid">
        <StatCard
          icon={Activity}
          label="Total evaluations"
          value={completed}
          color="purple"
          note="Saved evaluations"
        />

        <StatCard
          icon={ChartNoAxesCombined}
          label="Average quality score"
          value={average}
          suffix={average === '—' ? '' : '/10'}
          color="blue"
          note="Based on scored evaluations"
        />

        <StatCard
          icon={ShieldAlert}
          label="Hallucinations detected"
          value={hallucinations}
          color="red"
          note="From completed evaluations"
        />

        <StatCard
          icon={Bot}
          label="Evaluation agents"
          value="5"
          suffix="/5"
          color="green"
          note="Connected evaluation pipeline"
        />
      </section>

      <section className="charts-grid">
        <div className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Evaluation-wise performance</h3>
              <p>Overall score of every completed evaluation</p>
            </div>

            <span className="chart-tag">
              {chartData.length} evaluations
            </span>
          </div>

          <div className="chart-area">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient
                      id="scoreFill"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="#9b82ff"
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor="#9b82ff"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    stroke="#24283a"
                    strokeDasharray="3 5"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="name"
                    stroke="#777d91"
                    tickLine={false}
                    axisLine={false}
                  />

                  <YAxis
                    domain={[0, 10]}
                    stroke="#777d91"
                    tickLine={false}
                    axisLine={false}
                    allowDecimals
                  />

                  <Tooltip content={<EvaluationTooltip />} />

                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#a18aff"
                    strokeWidth={2.5}
                    fill="url(#scoreFill)"
                    activeDot={{ r: 6 }}
                    dot={{ r: 4 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState text="Your evaluation scores will appear here after your first completed evaluation." />
            )}
          </div>
        </div>

        <div className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Evaluation agents</h3>
              <p>Five specialized validation agents</p>
            </div>

            <span className="chart-tag">5 agents</span>
          </div>

          <div className="agent-mini-list">
            {agentDefinitions.map(agent => {
              const Icon = agent.icon

              return (
                <div className="agent-mini-row" key={agent.key}>
                  <span className={`mini-agent-icon ${agent.color}`}>
                    <Icon size={15} />
                  </span>

                  <span>{agent.name}</span>

                  <CheckCircle2 size={15} className="mini-check" />
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="panel recent-panel">
        <div className="panel-heading">
          <div>
            <h3>Recent evaluations</h3>
            <p>Your saved evaluation records</p>
          </div>

          <button
            className="text-button"
            onClick={() => setActive('History')}
          >
            View history <ArrowUpRight size={15} />
          </button>
        </div>

        {evaluations.length ? (
          <EvaluationTable evaluations={evaluations.slice(0, 5)} />
        ) : (
          <EmptyState text="No evaluations yet. Open Evaluation Studio to run your first test." />
        )}
      </section>
    </>
  )
}

// PAGE HEADING

function PageHeading({ eyebrow, title, description }) {
  return (
    <div className="page-heading">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p className="page-description">{description}</p>
    </div>
  )
}

// EVALUATION STUDIO

function EvaluationStudio({ onEvaluationComplete }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  async function runEvaluation(event) {
    event.preventDefault()
    setError('')
    setResult(null)

    if (!question.trim() || !answer.trim()) {
      setError('Please enter both the question and the AI-generated answer.')
      return
    }

    setLoading(true)

    try {
      const response = await api.post('/api/evaluate', {
        question: question.trim(),
        answer: answer.trim(),
        reference_answer: null,
      })

      const data = response.data

      const completedEvaluation = normalizeEvaluation({
        ...data,
        evaluation_id: data.evaluation_id,
        question: question.trim(),
        answer: answer.trim(),
      })

      setResult(completedEvaluation)

      onEvaluationComplete(completedEvaluation)
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        'Evaluation request failed.'

      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="EVALUATION WORKSPACE"
        title="Evaluation Studio"
        description="Submit an AI-generated answer and evaluate it using five specialized agents."
      />

      <div className="evaluation-layout">
        <form className="panel evaluation-form" onSubmit={runEvaluation}>
          <div className="form-heading">
            <FlaskConical size={20} />

            <div>
              <h3>New response evaluation</h3>
              <p>Enter the question and the answer you want to validate.</p>
            </div>
          </div>

          <label htmlFor="question">User question</label>

          <textarea
            id="question"
            rows="4"
            value={question}
            onChange={event => setQuestion(event.target.value)}
            placeholder="Example: What is the pre-existing disease waiting period in HDFC iCan Essential?"
            required
          />

          <label htmlFor="answer">AI-generated answer</label>

          <textarea
            id="answer"
            rows="7"
            value={answer}
            onChange={event => setAnswer(event.target.value)}
            placeholder="Paste the AI-generated answer here..."
            required
          />

          <div className="form-note">
            <Database size={15} />
            The backend retrieves relevant evidence from the indexed
            knowledge base and insurance dataset.
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            className="primary-button run-button"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <LoaderCircle className="spin" size={17} />
                Evaluating response...
              </>
            ) : (
              <>
                <Play size={16} />
                Run evaluation
              </>
            )}
          </button>
        </form>

        <div className="panel evaluation-info">
          <div className="panel-heading">
            <div>
              <h3>Evaluation workflow</h3>
              <p>How your response is validated</p>
            </div>

            <Sparkles size={20} className="purple-text" />
          </div>

          <div className="workflow-list">
            {agentDefinitions.map((agent, index) => (
              <div className="workflow-item" key={agent.key}>
                <div className={`workflow-number ${agent.color}`}>
                  {index + 1}
                </div>

                <div>
                  <strong>{agent.name}</strong>
                  <p>{agent.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {result && <EvaluationResults result={result} />}
    </>
  )
}

// EVALUATION RESULTS

function EvaluationResults({ result }) {
  const agents = result?.agents || {}
  const verdict = result?.final_verdict || agents.verdict

  const sections = [
    { key: 'relevance', title: 'Relevance Judge' },
    { key: 'accuracy', title: 'Accuracy Judge' },
    { key: 'hallucination', title: 'Hallucination Detector' },
    { key: 'completeness', title: 'Completeness Judge' },
    { key: 'verdict', title: 'Verdict Agent' },
  ]

  return (
    <section className="results-section">
      <div className="results-title">
        <div>
          <div className="eyebrow">EVALUATION COMPLETED</div>
          <h2>Evaluation report</h2>
        </div>

        <span
          className={`result-pill ${getVerdictClass(verdict?.final_verdict)}`}
        >
          {verdict?.final_verdict || 'No verdict'}
        </span>
      </div>

      <div className="final-score-panel">
        <div>
          <span className="muted-label">Overall quality score</span>

          <div className="big-score">
            {verdict?.overall_score ?? 'N/A'}
            <small>/10</small>
          </div>

          <p>{verdict?.reason || 'Evaluation completed.'}</p>
        </div>
      </div>

      <div className="result-agent-grid">
        {sections.map(agent => {
          const data = agents[agent.key] || {}
          const score = getScore(data)

          return (
            <div className="panel result-agent-card" key={agent.key}>
              <h3>{agent.title}</h3>

              {agent.key === 'hallucination' ? (
                <strong>
                  {data.hallucination_detected === true
                    ? 'Detected'
                    : data.hallucination_detected === false
                      ? 'Not detected'
                      : 'N/A'}
                </strong>
              ) : (
                <strong>{formatScore(score)}</strong>
              )}

              <p>
                {data.verdict ||
                  data.final_verdict ||
                  (data.hallucination_detected === false
                    ? 'No Hallucination'
                    : data.hallucination_detected === true
                      ? 'Hallucination Detected'
                      : 'Not available')}
              </p>

              <p>
                {data.explanation ||
                  data.reason ||
                  'No explanation available.'}
              </p>

              {data.supported_claims?.length > 0 && (
                <>
                  <strong>Supported claims</strong>
                  <ul>
                    {data.supported_claims.map((claim, i) => (
                      <li key={i}>{claim}</li>
                    ))}
                  </ul>
                </>
              )}

              {data.hallucinated_claims?.length > 0 && (
                <>
                  <strong>Hallucinated claims</strong>
                  <ul>
                    {data.hallucinated_claims.map((claim, i) => (
                      <li key={i}>{claim}</li>
                    ))}
                  </ul>
                </>
              )}

              {data.missing_information?.length > 0 && (
                <>
                  <strong>Missing information</strong>
                  <ul>
                    {data.missing_information.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )
        })}
      </div>

      {['strengths', 'issues'].map(key =>
        verdict?.[key]?.length > 0 ? (
          <div className="panel detail-panel" key={key}>
            <h3>
              {key === 'strengths' ? 'Overall strengths' : 'Issues to review'}
            </h3>

            <ul>
              {verdict[key].map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null
      )}

      <EvidencePanel evidence={result?.evidence} />
    </section>
  )
}

// EVIDENCE PANEL

function EvidencePanel({ evidence }) {
  const pdf = evidence?.pdf_evidence || []
  const csv = evidence?.csv_evidence || []
  const allEvidence = [...pdf, ...csv]

  return (
    <div className="panel evidence-panel">
      <div className="panel-heading">
        <div>
          <h3><Database size={17} /> Retrieved evidence</h3>
          <p>Source information used during response evaluation</p>
        </div>

        <span className="chart-tag">{allEvidence.length} items</span>
      </div>

      {allEvidence.length ? (
        <div className="evidence-list">
          {allEvidence.slice(0, 8).map((item, index) => (
            <div className="evidence-item" key={index}>
              <div className="evidence-meta">
                <FileText size={14} />
                <strong>{item.source || 'Knowledge base'}</strong>
                <span>Page: {item.page ?? 'N/A'}</span>
              </div>

              <p>{item.text || JSON.stringify(item)}</p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState text="No supporting evidence was returned for this evaluation." />
      )}
    </div>
  )
}

// KNOWLEDGE HUB

function KnowledgeHub() {
  const [filePath, setFilePath] = useState('backend/uploads/hdfc_policy.pdf')
  const [ingestLoading, setIngestLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const [company, setCompany] = useState('HDFC')
  const [minCoverage, setMinCoverage] = useState('')
  const [maxPremium, setMaxPremium] = useState('')
  const [cashless, setCashless] = useState('')
  const [dataset, setDataset] = useState([])
  const [totalResults, setTotalResults] = useState(0)
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [searched, setSearched] = useState(false)

  async function ingestDocument(event) {
    event.preventDefault()
    setMessage('')
    setError('')
    setIngestLoading(true)

    try {
      const response = await api.post('/api/ingest', {
        file_path: filePath.trim(),
      })

      const data = response.data

      setMessage(
        `${data.message || 'Ingestion completed.'} Chunks added: ${data.chunks_added ?? 'N/A'}`
      )
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message ||
        'Document ingestion failed.'
      )
    } finally {
      setIngestLoading(false)
    }
  }

  async function searchDataset(event) {
    event.preventDefault()
    setSearchError('')
    setSearchLoading(true)
    setSearched(true)

    try {
      const params = new URLSearchParams()

      if (company.trim()) params.append('company', company.trim())
      if (minCoverage) params.append('min_coverage', minCoverage)
      if (maxPremium) params.append('max_premium', maxPremium)
      if (cashless) params.append('cashless', cashless)

      const response = await api.get(
        `/api/dataset/search?${params.toString()}`
      )

      const data = response.data

      setDataset(Array.isArray(data.results) ? data.results : [])
      setTotalResults(data.total_results ?? 0)
    } catch (err) {
      setDataset([])
      setTotalResults(0)
      setSearchError(
        err.response?.data?.detail || err.message || 'Dataset search failed.'
      )
    } finally {
      setSearchLoading(false)
    }
  }

  function clearFilters() {
    setCompany('')
    setMinCoverage('')
    setMaxPremium('')
    setCashless('')
    setDataset([])
    setTotalResults(0)
    setSearched(false)
    setSearchError('')
  }

  function formatCurrency(value) {
    if (value === null || value === undefined) return 'N/A'

    return Number(value).toLocaleString('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    })
  }

  return (
    <>
      <PageHeading
        eyebrow="KNOWLEDGE & DATA MANAGEMENT"
        title="Knowledge Hub"
        description="Manage policy documents and explore structured insurance datasets."
      />

      <div className="dataset-section-heading">
        <div className="dataset-section-icon purple">
          <FileText size={19} />
        </div>

        <div>
          <h2>Policy Documents</h2>
          <p>Manage documents indexed by your RAG pipeline.</p>
        </div>
      </div>

      <div className="panel ingest-panel">
        <div className="form-heading">
          <Upload size={21} />

          <div>
            <h3>Ingest a policy document</h3>
            <p>Send a file path accessible to the backend server.</p>
          </div>
        </div>

        <form onSubmit={ingestDocument}>
          <label htmlFor="filePath">Backend file path</label>

          <input
            id="filePath"
            value={filePath}
            onChange={event => setFilePath(event.target.value)}
            placeholder="backend/uploads/your_policy.pdf"
            required
          />

          <p className="form-note">
            This endpoint accepts a backend file path, not a browser file upload.
          </p>

          {message && <div className="success-message">{message}</div>}
          {error && <div className="error-message">{error}</div>}

          <button
            className="primary-button"
            type="submit"
            disabled={ingestLoading}
          >
            {ingestLoading ? (
              <>
                <LoaderCircle className="spin" size={16} />
                Indexing...
              </>
            ) : (
              <>
                <Upload size={16} />
                Ingest document
              </>
            )}
          </button>
        </form>
      </div>

      <div className="panel document-panel">
        <h3>Project knowledge source</h3>

        <div className="document-row">
          <div className="document-icon"><FileText size={20} /></div>

          <div>
            <strong>HDFC iCan Essential Policy PDF</strong>
            <p>backend/uploads/hdfc_policy.pdf</p>
          </div>

          <span className="result-pill success">Project file</span>
        </div>
      </div>

      <div className="dataset-section-heading dataset-heading-spacing">
        <div className="dataset-section-icon green">
          <Database size={19} />
        </div>

        <div>
          <h2>Insurance Dataset Explorer</h2>
          <p>
            Search and explore structured insurance records from your CSV dataset.
          </p>
        </div>
      </div>

      <div className="panel dataset-panel">
        <div className="panel-heading">
          <div>
            <h3>Search insurance records</h3>
            <p>Apply filters to find matching insurance policies.</p>
          </div>

          <span className="chart-tag">CSV Dataset</span>
        </div>

        <form onSubmit={searchDataset}>
          <div className="dataset-filter-grid">
            <div>
              <label htmlFor="datasetCompany">Insurance company</label>
              <input
                id="datasetCompany"
                value={company}
                onChange={event => setCompany(event.target.value)}
                placeholder="Example: HDFC"
              />
            </div>

            <div>
              <label htmlFor="minCoverage">Minimum coverage (₹)</label>
              <input
                id="minCoverage"
                type="number"
                min="0"
                value={minCoverage}
                onChange={event => setMinCoverage(event.target.value)}
                placeholder="Example: 500000"
              />
            </div>

            <div>
              <label htmlFor="maxPremium">Maximum annual premium (₹)</label>
              <input
                id="maxPremium"
                type="number"
                min="0"
                value={maxPremium}
                onChange={event => setMaxPremium(event.target.value)}
                placeholder="Example: 100000"
              />
            </div>

            <div>
              <label htmlFor="cashless">Cashless availability</label>
              <select
                id="cashless"
                value={cashless}
                onChange={event => setCashless(event.target.value)}
              >
                <option value="">All</option>
                <option value="Yes">Available</option>
                <option value="No">Not available</option>
              </select>
            </div>
          </div>

          <div className="dataset-actions">
            <button
              type="submit"
              className="primary-button"
              disabled={searchLoading}
            >
              {searchLoading ? (
                <>
                  <LoaderCircle className="spin" size={16} />
                  Searching...
                </>
              ) : (
                <>
                  <Search size={16} />
                  Search Dataset
                </>
              )}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={clearFilters}
            >
              <RefreshCw size={15} />
              Clear filters
            </button>
          </div>
        </form>

        {searchError && <div className="error-message">{searchError}</div>}

        {searched && !searchLoading && !searchError && (
          <div className="dataset-result-summary">
            <div>
              <strong>{totalResults} records found</strong>
              <p>Matching records from the insurance CSV dataset.</p>
            </div>

            <span className="chart-tag">Search completed</span>
          </div>
        )}

        {dataset.length > 0 && (
          <div className="table-wrap dataset-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Policy Product</th>
                  <th>Coverage Amount</th>
                  <th>Annual Premium</th>
                  <th>Claim Settlement</th>
                  <th>Cashless</th>
                  <th>PED Cover</th>
                </tr>
              </thead>

              <tbody>
                {dataset.map((item, index) => (
                  <tr key={item.Policy_ID || index}>
                    <td>{item.Company || 'N/A'}</td>
                    <td className="question-cell">
                      {item.Policy_Product || 'N/A'}
                    </td>
                    <td className="score-cell">
                      {formatCurrency(item.Coverage_Amount)}
                    </td>
                    <td>{formatCurrency(item.Annual_Premium)}</td>
                    <td>
                      {item['Claim_Settlement_Ratio (%)'] ?? 'N/A'}%
                    </td>
                    <td>
                      <span
                        className={`result-pill ${
                          item.Cashless_Available === 'Yes'
                            ? 'success'
                            : 'warning'
                        }`}
                      >
                        {item.Cashless_Available || 'N/A'}
                      </span>
                    </td>
                    <td>{item.Pre_Existing_Disease_Cover || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {searched && !searchLoading && !searchError && dataset.length === 0 && (
          <EmptyState text="No matching insurance records found. Try changing your filters." />
        )}

        {!searched && (
          <EmptyState text="Enter a company name or filters above and click Search Dataset." />
        )}
      </div>
    </>
  )
}

// HISTORY PAGE

function HistoryPage({ evaluations, onSelect }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [filter, setFilter] = useState('All')

  const filteredEvaluations = evaluations.filter(item => {
    const question = (item.question || '').toLowerCase()
    const verdict = item.final_verdict?.final_verdict || ''

    const matchesSearch = question.includes(searchTerm.toLowerCase())

    const matchesFilter =
      filter === 'All' ||
      (filter === 'Pass' && verdict.toLowerCase().includes('pass')) ||
      (filter === 'Fail' && (
        verdict.toLowerCase().includes('fail') ||
        verdict.toLowerCase().includes('improvement')
      ))

    return matchesSearch && matchesFilter
  })

  const passCount = evaluations.filter(
    item =>
      (item.final_verdict?.final_verdict || '')
        .toLowerCase()
        .includes('pass')
  ).length

  const failCount = evaluations.filter(item => {
    const verdict = (item.final_verdict?.final_verdict || '').toLowerCase()
    return verdict.includes('fail') || verdict.includes('improvement')
  }).length

  const scored = evaluations.filter(item =>
    Number.isFinite(Number(item.final_verdict?.overall_score))
    && item.final_verdict?.overall_score !== null
    && item.final_verdict?.overall_score !== undefined
  )

  const averageScore = scored.length
    ? (
        scored.reduce(
          (sum, item) =>
            sum + Number(item.final_verdict.overall_score),
          0
        ) / scored.length
      ).toFixed(1)
    : '0.0'

  return (
    <>
      <PageHeading
        eyebrow="EVALUATION RECORDS"
        title="Evaluation History"
        description="Track, search and review your previous AI response evaluations."
      />

      <div className="history-stats">
        <div className="panel history-stat-card">
          <span>Total Evaluations</span>
          <strong>{evaluations.length}</strong>
          <small>All completed tests</small>
        </div>

        <div className="panel history-stat-card">
          <span>Passed Evaluations</span>
          <strong className="success-text">{passCount}</strong>
          <small>Responses marked Pass</small>
        </div>

        <div className="panel history-stat-card">
          <span>Failed / Needs Improvement</span>
          <strong className="danger-text">{failCount}</strong>
          <small>Responses needing review</small>
        </div>

        <div className="panel history-stat-card">
          <span>Average Score</span>
          <strong>{averageScore}<small>/10</small></strong>
          <small>Overall quality score</small>
        </div>
      </div>

      <div className="panel recent-panel history-main-panel">
        <div className="panel-heading">
          <div>
            <h3>All Evaluations</h3>
            <p>Search and review your evaluation reports.</p>
          </div>

          <span className="chart-tag">
            {filteredEvaluations.length} records
          </span>
        </div>

        <div className="history-toolbar">
          <div className="history-search">
            <Search size={17} />

            <input
              type="text"
              placeholder="Search by question..."
              value={searchTerm}
              onChange={event => setSearchTerm(event.target.value)}
            />
          </div>

          <select
            className="history-filter"
            value={filter}
            onChange={event => setFilter(event.target.value)}
          >
            <option value="All">All evaluations</option>
            <option value="Pass">Passed</option>
            <option value="Fail">Failed / Needs Improvement</option>
          </select>
        </div>

        {filteredEvaluations.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Evaluation Question</th>
                  <th>Date & Time</th>
                  <th>Quality Score</th>
                  <th>Final Verdict</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {filteredEvaluations.map(item => (
                  <tr key={item.id}>
                    <td className="question-cell">{item.question}</td>
                    <td className="table-muted">{item.createdAt || 'N/A'}</td>
                    <td className="score-cell">
                      {formatScore(item.final_verdict?.overall_score)}
                    </td>
                    <td>
                      <span
                        className={`result-pill ${getVerdictClass(
                          item.final_verdict?.final_verdict
                        )}`}
                      >
                        {item.final_verdict?.final_verdict || 'Unknown'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => onSelect(item)}
                      >
                        View Report <ArrowUpRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            text={
              evaluations.length
                ? 'No evaluations match your search or filter.'
                : 'No evaluation history yet. Complete your first evaluation to see it here.'
            }
          />
        )}
      </div>
    </>
  )
}

// ANALYTICS PAGE

function Analytics({ evaluations }) {
  const chartData = [...evaluations]
    .reverse()
    .map((item, index) => ({
      name: `Evaluation ${index + 1}`,
      score: Number(item.final_verdict?.overall_score),
      question: item.question,
      date: item.createdAt,
    }))
    .filter(item => Number.isFinite(item.score))

  const average = chartData.length
    ? (
        chartData.reduce((sum, item) => sum + item.score, 0) /
        chartData.length
      ).toFixed(1)
    : '—'

  const highest = chartData.length
    ? Math.max(...chartData.map(item => item.score))
    : '—'

  return (
    <>
      <PageHeading
        eyebrow="PERFORMANCE INSIGHTS"
        title="Analytics"
        description="Analyze the overall quality score of every completed evaluation."
      />

      <div className="history-stats">
        <div className="panel history-stat-card">
          <span>Total Evaluations</span>
          <strong>{chartData.length}</strong>
          <small>Evaluations with a score</small>
        </div>

        <div className="panel history-stat-card">
          <span>Average Score</span>
          <strong>{average}<small>{average === '—' ? '' : '/10'}</small></strong>
          <small>Across all evaluations</small>
        </div>

        <div className="panel history-stat-card">
          <span>Highest Score</span>
          <strong>{highest}<small>{highest === '—' ? '' : '/10'}</small></strong>
          <small>Best evaluation result</small>
        </div>
      </div>

      <div className="panel chart-panel analytics-chart">
        <div className="panel-heading">
          <div>
            <h3>Evaluation-wise overall scores</h3>
            <p>Each point represents one saved evaluation. Scores are out of 10.</p>
          </div>

          <ChartNoAxesCombined className="purple-text" />
        </div>

        <div className="chart-area">
          {chartData.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient
                    id="analyticsScoreFill"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#8e78ed" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8e78ed" stopOpacity={0} />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  stroke="#24283a"
                  strokeDasharray="3 5"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  stroke="#777d91"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  domain={[0, 10]}
                  stroke="#777d91"
                  tickLine={false}
                  axisLine={false}
                />

                <Tooltip content={<EvaluationTooltip />} />

                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#8e78ed"
                  strokeWidth={2.5}
                  fill="url(#analyticsScoreFill)"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="Run an evaluation to generate analytics." />
          )}
        </div>
      </div>

      <section className="panel recent-panel">
        <div className="panel-heading">
          <div>
            <h3>Evaluation score records</h3>
            <p>Individual overall scores from your saved evaluations.</p>
          </div>
        </div>

        {evaluations.length ? (
          <EvaluationTable evaluations={evaluations} />
        ) : (
          <EmptyState text="No evaluation records available yet." />
        )}
      </section>
    </>
  )
}

// SETTINGS PAGE

function SettingsPage({ apiStatus, checkBackend }) {
  const { user, logout } = useAuth()

  return (
    <>
      <PageHeading
        eyebrow="WORKSPACE CONFIGURATION"
        title="Settings"
        description="Account details, backend connection and project information."
      />

      <div className="panel settings-panel">
        <h3>Account information</h3>
        <p>Name: <strong>{user?.name || 'User'}</strong></p>
        <p>Email: <strong>{user?.email || 'N/A'}</strong></p>

        <button
          className="secondary-button"
          onClick={logout}
        >
          Logout
        </button>

        <div className="settings-divider" />

        <h3>Backend API connection</h3>
        <p>API endpoint: <strong>{API_BASE}</strong></p>

        <p>
          Status:
          <span className={apiStatus ? 'success-text' : 'danger-text'}>
            {apiStatus ? ' Connected' : ' Not connected'}
          </span>
        </p>

        <button className="primary-button" onClick={checkBackend}>
          <RefreshCw size={16} />
          Check connection
        </button>

        <div className="settings-divider" />

        <h3>Project information</h3>
        <p>
          Development of AI Response Validation System with Hallucination
          Detection Assistance.
        </p>
        <p>Backend: Python, FastAPI, RAG, ChromaDB and Groq.</p>
        <p>Frontend: React, Vite and Recharts.</p>
      </div>
    </>
  )
}

// MAIN APP

export default function App() {
  const { isAuthenticated } = useAuth()

  const [active, setActive] = useState('Dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [apiStatus, setApiStatus] = useState(false)

  const [evaluations, setEvaluations] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)

  async function checkBackend() {
    try {
      const response = await api.get('/api/health')
      setApiStatus(response.status === 200)
    } catch (error) {
      console.error('Backend health check failed:', error)
      setApiStatus(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      checkBackend()
    }
  }, [isAuthenticated])

  // Load the logged-in user's saved evaluations from backend.
  useEffect(() => {
    if (!isAuthenticated) {
      setEvaluations([])
      setSelectedReport(null)
      return
    }

    let cancelled = false

    async function loadHistory() {
      try {
        const response = await api.get('/api/evaluations/my-history')

        const records = response.data.evaluations || []
        const formattedRecords = records.map(normalizeEvaluation)

        if (!cancelled) {
          setEvaluations(formattedRecords)
        }
      } catch (error) {
        console.error('Could not load evaluation history:', error)
      }
    }

    loadHistory()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  function addEvaluation(item) {
    const normalized = normalizeEvaluation(item)

    setEvaluations(previous => [
      normalized,
      ...previous.filter(existing => String(existing.id) !== String(normalized.id)),
    ])

    setSelectedReport(null)
  }

  function openReport(item) {
    setSelectedReport(item)
    setActive('Evaluation Studio')
  }

  const latestResult = useMemo(
    () => selectedReport || evaluations[0] || null,
    [selectedReport, evaluations]
  )

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute />}>
        <Route
          path="*"
          element={
            <div className="app-shell">
              <Sidebar
                active={active}
                setActive={setActive}
                open={menuOpen}
                setOpen={setMenuOpen}
              />

              <main className="main-area">
                <header className="topbar">
                  <button
                    className="mobile-menu"
                    onClick={() => setMenuOpen(true)}
                  >
                    <Menu size={21} />
                  </button>

                  <div className="breadcrumb">
                    Workspace <span>/</span> <strong>{active}</strong>
                  </div>

                  <div className="topbar-actions">
                    <div className="system-status">
                      <span
                        className={`live-dot ${
                          apiStatus ? '' : 'offline-dot'
                        }`}
                      />

                      {apiStatus ? 'Backend connected' : 'Backend offline'}
                    </div>

                    <button
                      className="icon-button"
                      aria-label="Notifications"
                    >
                      <Bell size={18} />
                    </button>

                    <div className="top-avatar">AV</div>
                  </div>
                </header>

                <div className="content-area">
                  {active === 'Dashboard' && (
                    <Dashboard
                      evaluations={evaluations}
                      apiStatus={apiStatus}
                      setActive={setActive}
                    />
                  )}

                  {active === 'Evaluation Studio' && (
                    <>
                      {selectedReport ? (
                        <>
                          <PageHeading
                            eyebrow="SAVED SESSION REPORT"
                            title="Evaluation report"
                            description="Previously completed evaluation."
                          />

                          <EvaluationResults result={selectedReport} />

                          <button
                            className="secondary-button"
                            onClick={() => setSelectedReport(null)}
                          >
                            <Plus size={15} />
                            Start a new evaluation
                          </button>
                        </>
                      ) : (
                        <EvaluationStudio
                          onEvaluationComplete={addEvaluation}
                        />
                      )}
                    </>
                  )}

                  {active === 'Agent Analysis' && (
                    <AgentAnalysis latestResult={latestResult} />
                  )}

                  {active === 'Knowledge Hub' && <KnowledgeHub />}

                  {active === 'History' && (
                    <HistoryPage
                      evaluations={evaluations}
                      onSelect={openReport}
                    />
                  )}

                  {active === 'Analytics' && (
                    <Analytics evaluations={evaluations} />
                  )}

                  {active === 'Settings' && (
                    <SettingsPage
                      apiStatus={apiStatus}
                      checkBackend={checkBackend}
                    />
                  )}
                </div>

                <footer className="footer">
                  <span>© 2026 AI Response Validation System</span>
                  <span>Intelligent response validation platform</span>
                </footer>
              </main>
            </div>
          }
        />
      </Route>
    </Routes>
  )
}
