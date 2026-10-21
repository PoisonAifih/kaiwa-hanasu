import type { ReactNode } from 'react'
import type { Correction, CorrectionState, Issue, IssueCategory } from '../lib/types.ts'

const CATEGORY_LABELS: Record<IssueCategory, string> = {
  grammar: 'Grammar',
  particle: 'Particle',
  word_choice: 'Word choice',
  politeness: 'Politeness',
  naturalness: 'Naturalness',
}

type Props = {
  check: CorrectionState
  hearing: boolean
  onHear(text: string): void
  onRetry(): void
}

export function CorrectionCard({ check, hearing, onHear, onRetry }: Props) {
  if (check.status === 'checking') {
    return <div className="correction correction-muted">Checking your Japanese…</div>
  }
  if (check.status === 'failed') {
    return (
      <div className="correction correction-muted">
        Couldn't check this one.{' '}
        <button type="button" className="link-button" onClick={onRetry}>
          Retry
        </button>
      </div>
    )
  }
  const { correction } = check
  if (correction.ok) {
    return <div className="correction correction-ok">✓ Looks good</div>
  }
  return (
    <div className="correction correction-fix">
      <div className="correction-row">
        <span className="correction-label">As said</span>
        <span lang="ja">{highlightSpans(correction)}</span>
      </div>
      <div className="correction-row">
        <span className="correction-label">Natural</span>
        <span lang="ja" className="correction-natural">
          {correction.corrected}
        </span>
        <button
          type="button"
          className="icon-button"
          onClick={() => onHear(correction.corrected)}
          aria-label="Hear the natural version"
          title="Hear the natural version"
        >
          {hearing ? '■' : '🔊'}
        </button>
      </div>
      {correction.issues.length > 0 && (
        <ul className="issues">
          {correction.issues.map((issue, i) => (
            <IssueItem key={i} issue={issue} />
          ))}
        </ul>
      )}
    </div>
  )
}

function IssueItem({ issue }: { issue: Issue }) {
  return (
    <li>
      <span className={`badge badge-${issue.category}`}>{CATEGORY_LABELS[issue.category]}</span>
      {issue.original_span && issue.suggestion && (
        <span lang="ja" className="issue-change">
          <s>{issue.original_span}</s> → {issue.suggestion}
        </span>
      )}
      <span className="issue-note">{issue.note}</span>
    </li>
  )
}

// Issue highlights
function highlightSpans(correction: Correction): ReactNode[] {
  const text = correction.original
  const spans = correction.issues
    .filter((issue) => issue.start !== null && issue.end !== null)
    .sort((a, b) => a.start! - b.start!)
  const parts: ReactNode[] = []
  let cursor = 0
  for (const issue of spans) {
    if (issue.start! < cursor) continue
    parts.push(text.slice(cursor, issue.start!))
    parts.push(
      <mark key={issue.start} className={`mark-${issue.category}`}>
        {text.slice(issue.start!, issue.end!)}
      </mark>,
    )
    cursor = issue.end!
  }
  parts.push(text.slice(cursor))
  return parts
}
