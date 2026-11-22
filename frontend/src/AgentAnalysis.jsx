
import {
  Bot,
  Search,
  CheckCircle2,
  ShieldAlert,
  FileText,
  Sparkles,
  Database,
} from 'lucide-react'

import './AgentAnalysis.css'

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

function getScore(data) {
  if (!data) return null
  return data.score ?? data.overall_score ?? null
}

function formatScore(score) {
  return score === null || score === undefined
    ? 'N/A'
    : `${score}/10`
}

function getVerdictClass(verdict = '') {
  const value = String(verdict).toLowerCase()

  if (
    value.includes('pass') ||
    value.includes('correct') ||
    value.includes('relevant') ||
    value.includes('complete') ||
    value.includes('no hallucination')
  ) {
    return 'aa-success'
  }

  if (
    value.includes('partial') ||
    value.includes('improvement') ||
    value.includes('insufficient')
  ) {
    return 'aa-warning'
  }

  if (
    value.includes('fail') ||
    value.includes('incorrect') ||
    value.includes('not relevant') ||
    value.includes('hallucination detected') ||
    value.includes('incomplete')
  ) {
    return 'aa-danger'
  }

  return 'aa-neutral'
}

function PageHeading({ eyebrow, title, description }) {
  return (
    <div className="page-heading">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p className="page-description">{description}</p>
    </div>
  )
}

function ClaimList({ title, items, type = 'supported' }) {
  if (!Array.isArray(items) || items.length === 0) return null

  return (
    <div className="aa-claim-section">
      <h4>{title}</h4>
      <ul className={`aa-claim-list ${type}`}>
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>
            {typeof item === 'object' && item !== null
              ? item.claim || item.text || item.description || JSON.stringify(item)
              : String(item)}
          </li>
        ))}
      </ul>
    </div>
  )
}


function AgentCard({ agent, data }) {
  const Icon = agent.icon
  const score = getScore(data)

  const isHallucination = agent.key === 'hallucination'

  const status = isHallucination
    ? data?.hallucination_detected === true
      ? 'Hallucination Detected'
      : data?.hallucination_detected === false
        ? 'No Hallucination'
        : data?.verdict || 'Not available'
    : data?.verdict || data?.final_verdict || 'Not available'

  const metric = isHallucination
    ? data?.hallucination_detected === true
      ? 'Detected'
      : data?.hallucination_detected === false
        ? 'Clear'
        : 'N/A'
    : formatScore(score)

  return (
    <article className="panel aa-agent-card">
      <div className="aa-agent-heading">
        <div className={`aa-agent-icon ${agent.color}`}>
          <Icon size={20} />
        </div>

        <div className="aa-agent-title">
          <h3>{agent.name}</h3>
          <p>{agent.detail}</p>
        </div>

        <strong className="aa-agent-score">
          {metric}
        </strong>
      </div>

      {!data ? (
        <div className="aa-no-data">
          No result was returned by this agent.
        </div>
      ) : (
        <>
          <div className="aa-agent-status">
            <span>Agent verdict</span>
            <span className={`aa-status-pill ${getVerdictClass(status)}`}>
              {status}
            </span>
          </div>

          {isHallucination && (
            <div className={`aa-hallucination ${
              data.hallucination_detected === true
                ? 'detected'
                : data.hallucination_detected === false
                  ? 'clear'
                  : ''
            }`}>
              <ShieldAlert size={17} />
              {data.hallucination_detected === true
                ? 'Unsupported or fabricated claims detected.'
                : data.hallucination_detected === false
                  ? 'No hallucination detected.'
                  : 'Hallucination status unavailable.'}
            </div>
          )}

          <div className="aa-explanation">
            <h4>Agent explanation</h4>
            <p>
              {data.explanation ||
                data.reason ||
                'No explanation returned by the agent.'}
            </p>
          </div>

          {agent.key === 'accuracy' && (
            <>
              <ClaimList title="Supported claims" items={data.supported_claims} type="supported" />
              <ClaimList title="Unsupported claims" items={data.unsupported_claims} type="warning" />
              <ClaimList title="Contradicted claims" items={data.contradicted_claims} type="danger" />
            </>
          )}

          {isHallucination && (
            <>
              <ClaimList title="Supported claims" items={data.supported_claims} type="supported" />
              <ClaimList title="Hallucinated claims" items={data.hallucinated_claims} type="danger" />
            </>
          )}

          {agent.key === 'completeness' && (
            <ClaimList title="Missing information" items={data.missing_information} type="warning" />
          )}

          {agent.key === 'verdict' && (
            <>
              <ClaimList title="Strengths" items={data.strengths} type="supported" />
              <ClaimList title="Issues to review" items={data.issues} type="danger" />
            </>
          )}
        </>
      )}
    </article>
  )
}

function EvidenceOverview({ evidence, evidenceCount }) {
  const pdf = evidence?.pdf_evidence || []
  const csv = evidence?.csv_evidence || []
  const allEvidence = [...pdf, ...csv]

  return (
    <section className="panel aa-evidence-panel">
      <div className="panel-heading">
        <div>
          <h3><Database size={17} /> Retrieved evidence</h3>
          <p>Knowledge base information used during evaluation.</p>
        </div>
        <span className="chart-tag">{allEvidence.length} items</span>
      </div>

      <div className="aa-evidence-stats">
        <div>
          <span>Agent evidence count</span>
          <strong>{evidenceCount ?? 'N/A'}</strong>
        </div>
        <div>
          <span>PDF evidence</span>
          <strong>{pdf.length}</strong>
        </div>
        <div>
          <span>CSV evidence</span>
          <strong>{csv.length}</strong>
        </div>
      </div>

      {allEvidence.length > 0 ? (
        <div className="aa-evidence-list">
          {allEvidence.slice(0, 8).map((item, index) => (
            <div className="aa-evidence-item" key={index}>
              <div className="aa-evidence-meta">
                <FileText size={14} />
                <strong>{item.source || 'Knowledge base'}</strong>
                <span>Page: {item.page ?? 'N/A'}</span>
              </div>
              <p>{item.text || JSON.stringify(item)}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="aa-no-evidence">
          No PDF or CSV evidence was returned.
        </p>
      )}
    </section>
  )
}

export default function AgentAnalysis({ latestResult }) {
  const agents = latestResult?.agents || {}
  const verdict = latestResult?.final_verdict || agents.verdict

  if (!latestResult) {
    return (
      <>
        <PageHeading
          eyebrow="MULTI-AGENT SYSTEM"
          title="Agent Analysis"
          description="Understand the findings of your five specialized evaluation agents."
        />

        <div className="panel aa-empty-state">
          <Bot size={38} />
          <h3>No evaluation results available</h3>
          <p>
            Open Evaluation Studio and run an evaluation first.
            Your five agents' actual findings will appear here.
          </p>
        </div>
      </>
    )
  }

  return (
    <>
      <PageHeading
        eyebrow="MULTI-AGENT INTELLIGENCE"
        title="Agent Analysis"
        description="Explore detailed scores, findings, claims and explanations from your latest evaluation."
      />

      <section className="panel aa-summary">
        <div>
          <span className="muted-label">Overall quality score</span>

          <div className="big-score">
            {verdict?.overall_score ?? 'N/A'}
            <small>/10</small>
          </div>

          <p>{verdict?.reason || 'Evaluation completed.'}</p>
        </div>

        <span className={`aa-status-pill ${
          getVerdictClass(verdict?.final_verdict)
        }`}>
          {verdict?.final_verdict || 'No verdict'}
        </span>
      </section>

      <div className="aa-section-heading">
        <h2>Individual agent reports</h2>
        <p>Actual responses received from the backend agents.</p>
      </div>

      <div className="aa-agent-grid">
        {agentDefinitions.map(agent => (
          <AgentCard
            key={agent.key}
            agent={agent}
            data={agents[agent.key]}
          />
        ))}
      </div>

      {verdict?.strengths?.length > 0 && (
        <section className="panel aa-extra-panel">
          <h3><CheckCircle2 size={17} /> Overall strengths</h3>
          <ClaimList items={verdict.strengths} type="supported" />
        </section>
      )}

      {verdict?.issues?.length > 0 && (
        <section className="panel aa-extra-panel">
          <h3><ShieldAlert size={17} /> Overall issues</h3>
          <ClaimList items={verdict.issues} type="danger" />
        </section>
      )}

      <EvidenceOverview
        evidence={latestResult.evidence}
        evidenceCount={latestResult.agent_evidence_count}
      />
    </>
  )
}
