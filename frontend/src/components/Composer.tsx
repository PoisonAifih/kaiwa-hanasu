import { forwardRef, type KeyboardEvent } from 'react'
import { toKana } from 'wanakana'
import { MicButton } from './MicButton.tsx'

type Props = {
  draft: string
  kanaInput: boolean
  deviceId: string
  phase: 'idle' | 'transcribing' | 'replying'
  onDraftChange(text: string): void
  onSend(): void
  onRecordStart(): void
  onRecorded(blob: Blob): void
  onError(message: string): void
}

const PHASE_HINTS = {
  idle: 'Hold the mic (or Space) to speak — you can edit the text before sending.',
  transcribing: 'Listening back…',
  replying: 'Thinking of a reply…',
}

export const Composer = forwardRef<HTMLTextAreaElement, Props>(function Composer(
  { draft, kanaInput, deviceId, phase, onDraftChange, onSend, onRecordStart, onRecorded, onError },
  ref,
) {
  const busy = phase !== 'idle'

  function sendOnEnter(event: KeyboardEvent<HTMLTextAreaElement>) {
    // IME guard
    if (event.key !== 'Enter' || event.shiftKey || event.nativeEvent.isComposing) return
    event.preventDefault()
    if (!busy) onSend()
  }

  return (
    <footer className="composer">
      <div className="composer-row">
        <MicButton
          deviceId={deviceId}
          disabled={busy}
          onStart={onRecordStart}
          onRecorded={onRecorded}
          onError={onError}
        />
        <textarea
          ref={ref}
          className="composer-input"
          lang="ja"
          rows={1}
          value={draft}
          placeholder={kanaInput ? 'Type romaji: konnichiha → こんにちは' : '日本語で話しましょう…'}
          onChange={(event) =>
            onDraftChange(kanaInput ? toKana(event.target.value, { IMEMode: true }) : event.target.value)
          }
          onKeyDown={sendOnEnter}
        />
        <button type="button" className="send-button" disabled={busy || !draft.trim()} onClick={onSend}>
          Send
        </button>
      </div>
      <div className="composer-hint" aria-live="polite">
        {PHASE_HINTS[phase]}
      </div>
    </footer>
  )
})
