import { useCallback, useEffect, useRef, useState } from 'react'
import { Recorder, TooQuietError } from '../lib/recorder.ts'

// Tap vs hold
const TAP_MS = 300

type Props = {
  deviceId: string
  disabled: boolean
  onStart(): void
  onRecorded(blob: Blob): void
  onError(message: string): void
}

function describeMicError(error: unknown): string {
  if (error instanceof TooQuietError) return error.message
  if (error instanceof DOMException && error.name === 'NotAllowedError') {
    return 'Microphone access was blocked. Allow it in the browser address bar.'
  }
  if (error instanceof DOMException && error.name === 'NotFoundError') {
    return 'No microphone found. Pick another one in settings.'
  }
  return 'Could not use the microphone.'
}

function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
}

export function MicButton({ deviceId, disabled, onStart, onRecorded, onError }: Props) {
  const [recording, setRecording] = useState(false)
  const pending = useRef<Promise<Recorder> | null>(null)
  const pressedAt = useRef(0)
  const tapped = useRef(false)
  const spaceHeld = useRef(false)

  const begin = useCallback(async () => {
    if (pending.current || disabled) return
    onStart()
    const started = Recorder.start(deviceId)
    pending.current = started
    setRecording(true)
    try {
      await started
    } catch (error) {
      if (pending.current === started) pending.current = null
      setRecording(false)
      onError(describeMicError(error))
    }
  }, [deviceId, disabled, onStart, onError])

  const finish = useCallback(async () => {
    const started = pending.current
    if (!started) return
    pending.current = null
    tapped.current = false
    setRecording(false)
    try {
      const recording = await (await started).stop()
      onRecorded(recording.blob)
    } catch (error) {
      onError(describeMicError(error))
    }
  }, [onRecorded, onError])

  const cancel = useCallback(() => {
    const started = pending.current
    pending.current = null
    tapped.current = false
    setRecording(false)
    started?.then((recorder) => recorder.cancel()).catch(() => {})
  }, [])

  // Keyboard: Space / Escape
  useEffect(() => {
    const down = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && pending.current) cancel()
      if (event.code !== 'Space' || event.repeat || isTyping(event.target)) return
      event.preventDefault()
      if (pending.current) return
      spaceHeld.current = true
      void begin()
    }
    const up = (event: KeyboardEvent) => {
      if (event.code !== 'Space' || !spaceHeld.current) return
      event.preventDefault()
      spaceHeld.current = false
      void finish()
    }
    window.addEventListener('keydown', down)
    window.addEventListener('keyup', up)
    return () => {
      window.removeEventListener('keydown', down)
      window.removeEventListener('keyup', up)
    }
  }, [begin, finish, cancel])

  useEffect(() => cancel, [cancel])

  return (
    <button
      type="button"
      className={`mic-button${recording ? ' recording' : ''}`}
      disabled={disabled && !recording}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId)
        if (tapped.current) {
          void finish()
          return
        }
        pressedAt.current = performance.now()
        void begin()
      }}
      onPointerUp={() => {
        if (!pending.current || tapped.current) return
        if (performance.now() - pressedAt.current < TAP_MS) {
          tapped.current = true
          return
        }
        void finish()
      }}
      onContextMenu={(event) => event.preventDefault()}
      aria-label={recording ? 'Stop recording' : 'Record (hold, or tap to start)'}
      title="Hold to talk, or tap to start and tap again to stop. Space works too."
    >
      <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
        <path
          fill="currentColor"
          d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z"
        />
      </svg>
    </button>
  )
}
