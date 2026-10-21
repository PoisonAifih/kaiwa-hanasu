import { useEffect, useRef } from 'react'
import type { ChatMessage, Token, UserMessage } from '../lib/types.ts'
import { wordKey } from '../lib/words.ts'
import { CorrectionCard } from './CorrectionCard.tsx'
import { GlossedMessage } from './GlossedMessage.tsx'

export type SelectedWord = { messageId: string; key: string }

type Props = {
  messages: ChatMessage[]
  replying: boolean
  showFurigana: boolean
  panelMessageId: string | null
  selected: SelectedWord | null
  playingId: string | null
  onSelect(selection: SelectedWord): void
  onFocusMessage(id: string): void
  onPlay(id: string, text: string): void
  onRetryCheck(message: UserMessage): void
}

export function correctionAudioId(messageId: string): string {
  return `${messageId}:fix`
}

export function ChatThread(props: Props) {
  const { messages, replying, showFurigana, panelMessageId, selected, playingId } = props
  const { onSelect, onFocusMessage, onPlay, onRetryCheck } = props
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, replying])

  return (
    <div className="thread" role="log" aria-live="polite">
      {messages.map((message) =>
        message.role === 'user' ? (
          <div key={message.id} className="bubble-row user">
            <div className="bubble user-bubble" lang="ja">
              {message.text}
            </div>
            <CorrectionCard
              check={message.check}
              hearing={playingId === correctionAudioId(message.id)}
              onHear={(text) => onPlay(correctionAudioId(message.id), text)}
              onRetry={() => onRetryCheck(message)}
            />
          </div>
        ) : (
          <div key={message.id} className="bubble-row ai">
            {/* AI reply */}
            <div
              className={`bubble ai-bubble${panelMessageId === message.id ? ' in-panel' : ''}`}
              lang="ja"
              onClick={() => onFocusMessage(message.id)}
            >
              <GlossedMessage
                text={message.text}
                tokens={message.tokens}
                showFurigana={showFurigana}
                selectedKey={selected?.messageId === message.id ? selected.key : null}
                onSelect={(token: Token) => onSelect({ messageId: message.id, key: wordKey(token) })}
              />
              <button
                type="button"
                className="icon-button play-button"
                onClick={(event) => {
                  event.stopPropagation()
                  onPlay(message.id, message.text)
                }}
                aria-label={playingId === message.id ? 'Stop' : 'Play reply'}
                title={playingId === message.id ? 'Stop' : 'Play'}
              >
                {playingId === message.id ? '■' : '▶'}
              </button>
            </div>
          </div>
        ),
      )}
      {replying && (
        <div className="bubble-row ai">
          <div className="bubble ai-bubble typing" aria-label="Hanasu is replying">
            <span />
            <span />
            <span />
          </div>
        </div>
      )}
      <div ref={end} />
    </div>
  )
}
