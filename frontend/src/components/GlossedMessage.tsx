import type { ReactNode } from 'react'
import type { FuriganaSegment, Token } from '../lib/types.ts'
import { wordKey } from '../lib/words.ts'

export function Furigana({ segments, show }: { segments: FuriganaSegment[]; show: boolean }) {
  return (
    <>
      {segments.map((segment, i) =>
        segment.ruby && show ? (
          <ruby key={i}>
            {segment.text}
            <rt>{segment.ruby}</rt>
          </ruby>
        ) : (
          <span key={i}>{segment.text}</span>
        ),
      )}
    </>
  )
}

type Props = {
  text: string
  tokens: Token[]
  showFurigana: boolean
  selectedKey: string | null
  onSelect(token: Token): void
}

// Reply text
export function GlossedMessage({ text, tokens, showFurigana, selectedKey, onSelect }: Props) {
  // Plain fallback
  if (tokens.length === 0) return <p className="ai-text">{text}</p>
  const parts: ReactNode[] = []
  let cursor = 0
  for (const token of tokens) {
    if (token.start > cursor) parts.push(text.slice(cursor, token.start))
    const word = <Furigana segments={token.furigana} show={showFurigana} />
    parts.push(
      token.gloss ? (
        <button
          key={token.start}
          type="button"
          className={`word${selectedKey === wordKey(token) ? ' active' : ''}`}
          onClick={(event) => {
            event.stopPropagation()
            onSelect(token)
          }}
          aria-label={`${token.surface}: show meaning`}
        >
          {word}
        </button>
      ) : (
        <span key={token.start}>{word}</span>
      ),
    )
    cursor = token.end
  }
  if (cursor < text.length) parts.push(text.slice(cursor))
  return <p className={`ai-text${showFurigana ? ' with-furigana' : ''}`}>{parts}</p>
}
