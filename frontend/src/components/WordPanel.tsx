import { useEffect, useRef } from 'react'
import type { AiMessage } from '../lib/types.ts'
import { listVocabulary, shortenGloss, wordKey } from '../lib/words.ts'
import { Furigana } from './GlossedMessage.tsx'
import { WordSenses } from './WordSenses.tsx'

type Props = {
  message: AiMessage | null
  isLatest: boolean
  selectedKey: string | null
  showFurigana: boolean
  open: boolean
  onSelect(key: string | null): void
  onClose(): void
}

export function WordPanel({ message, isLatest, selectedKey, showFurigana, open, onSelect, onClose }: Props) {
  const items = useRef(new Map<string, HTMLLIElement>())
  const words = message ? listVocabulary(message.tokens) : []

  useEffect(() => {
    if (selectedKey) items.current.get(selectedKey)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [selectedKey, message?.id])

  return (
    <aside className={`word-panel${open ? ' open' : ''}`} aria-label="Words and meanings">
      <header className="word-panel-head">
        <div>
          <h2>Words</h2>
          <div className="muted word-panel-sub">{isLatest ? 'Latest reply' : 'Earlier reply'}</div>
        </div>
        <button type="button" className="icon-button word-panel-close" onClick={onClose} aria-label="Close words">
          ✕
        </button>
      </header>
      {message?.translation && (
        <section className="sentence-meaning" aria-label="Sentence meaning">
          <h3>Meaning</h3>
          <p>{message.translation}</p>
        </section>
      )}
      {words.length === 0 ? (
        <p className="muted word-panel-empty">
          {message ? 'No dictionary words in this reply.' : 'Words from the AI’s replies show up here.'}
        </p>
      ) : (
        <ul className="vocab">
          {words.map((token) => {
            const key = wordKey(token)
            const selected = key === selectedKey
            const conjugated = token.lemma !== token.surface
            return (
              <li
                key={key}
                ref={(node) => {
                  if (node) items.current.set(key, node)
                  else items.current.delete(key)
                }}
                className={selected ? 'selected' : undefined}
              >
                <button
                  type="button"
                  className="vocab-row"
                  onClick={() => onSelect(selected ? null : key)}
                  aria-expanded={token.entry_id !== null ? selected : undefined}
                >
                  <span className="vocab-word" lang="ja">
                    {conjugated ? token.lemma : <Furigana segments={token.furigana} show={showFurigana} />}
                    {conjugated && <span className="vocab-surface">{token.surface}</span>}
                  </span>
                  <span className="vocab-gloss">{shortenGloss(token.gloss!)}</span>
                </button>
                {selected && token.entry_id !== null && <WordSenses entryId={token.entry_id} />}
              </li>
            )
          })}
        </ul>
      )}
      <p className="attribution">Meanings from JMdict (EDRDG, CC BY-SA 4.0)</p>
    </aside>
  )
}
