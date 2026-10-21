import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ChatThread, type SelectedWord } from './components/ChatThread.tsx'
import { Composer } from './components/Composer.tsx'
import { SettingsPanel } from './components/SettingsPanel.tsx'
import { WordPanel } from './components/WordPanel.tsx'
import { api, ApiError } from './lib/api.ts'
import { SpeechPlayer } from './lib/speechPlayer.ts'
import { loadHistory, loadSettings, saveHistory, saveSettings } from './lib/storage.ts'
import type { AiMessage, ChatMessage, Scenario, Settings, UserMessage } from './lib/types.ts'

type Phase = 'idle' | 'transcribing' | 'replying'

const SCENARIO_LABELS: Record<Scenario, string> = {
  free: 'Free talk',
  self_intro: 'Self-introduction',
  cafe: 'Ordering at a café',
  weekend: 'Weekend plans',
}

function newId(): string {
  return crypto.randomUUID()
}

function describeError(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong.'
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

// Correction context
function findPartnerLine(messages: ChatMessage[], userId: string): string | null {
  const index = messages.findIndex((m) => m.id === userId)
  for (let i = index - 1; i >= 0; i -= 1) {
    if (messages[i]!.role === 'assistant') return messages[i]!.text
  }
  return null
}

export default function App() {
  const [settings, setSettings] = useState<Settings>(loadSettings)
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory)
  const [draft, setDraft] = useState('')
  // Busy states
  const [replying, setReplying] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const phase: Phase = replying ? 'replying' : transcribing ? 'transcribing' : 'idle'
  const [error, setError] = useState<{ message: string; retry?: () => void } | null>(null)
  const [selected, setSelected] = useState<SelectedWord | null>(null)
  // Word panel (null = latest reply)
  const [focusedId, setFocusedId] = useState<string | null>(null)
  // Mobile sheet
  const [wordsOpen, setWordsOpen] = useState(false)
  const [playingId, setPlayingId] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const player = useMemo(() => new SpeechPlayer(), [])
  const chatAbort = useRef<AbortController | null>(null)
  const input = useRef<HTMLTextAreaElement>(null)
  // Latest values for async callbacks
  const settingsRef = useRef(settings)
  settingsRef.current = settings
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  useEffect(() => saveSettings(settings), [settings])
  useEffect(() => saveHistory(messages), [messages])

  const play = useCallback(
    (id: string, text: string) => {
      if (playingId === id) {
        player.stop()
        setPlayingId(null)
        return
      }
      setPlayingId(id)
      player
        .speak(text)
        .catch((err) => setError({ message: `Voice failed: ${describeError(err)}` }))
        .finally(() => setPlayingId((current) => (current === id ? null : current)))
    },
    [player, playingId],
  )

  const requestReply = useCallback(
    async (history: ChatMessage[]) => {
      chatAbort.current?.abort()
      const controller = new AbortController()
      chatAbort.current = controller
      const { level, scenario } = settingsRef.current
      setReplying(true)
      setError(null)
      const pendingUser = history.at(-1)?.role === 'user' ? history.at(-1)!.id : null
      try {
        const response = await api.chat(history, { level, scenario, signal: controller.signal })
        // Stale response
        if (controller.signal.aborted) return
        const reply: AiMessage = {
          id: newId(),
          role: 'assistant',
          text: response.reply,
          translation: response.translation,
          tokens: response.tokens,
        }
        setMessages((current) => [
          ...current.map((m) =>
            m.id === pendingUser && m.role === 'user'
              ? {
                  ...m,
                  check: response.correction
                    ? { status: 'done' as const, correction: response.correction }
                    : { status: 'failed' as const },
                }
              : m,
          ),
          reply,
        ])
        setFocusedId(null)
        setSelected(null)
        // Autoplay
        if (settingsRef.current.voice && player.canAutoplay) {
          setPlayingId(reply.id)
          player
            .speak(reply.text)
            .catch((err) => setError({ message: `Voice failed: ${describeError(err)}` }))
            .finally(() => setPlayingId((current) => (current === reply.id ? null : current)))
        }
      } catch (err) {
        if (isAbort(err) || controller.signal.aborted) return
        setMessages((current) =>
          current.map((m) => (m.id === pendingUser && m.role === 'user' ? { ...m, check: { status: 'failed' } } : m)),
        )
        setError({
          message: describeError(err),
          retry: () => {
            const restored = messagesRef.current.map((m) =>
              m.id === pendingUser && m.role === 'user' ? { ...m, check: { status: 'checking' as const } } : m,
            )
            setMessages(restored)
            void requestReply(restored)
          },
        })
      } finally {
        if (chatAbort.current === controller) {
          chatAbort.current = null
          setReplying(false)
        }
      }
    },
    [player],
  )

  const startConversation = useCallback(() => {
    chatAbort.current?.abort()
    chatAbort.current = null
    player.stop()
    setPlayingId(null)
    setSelected(null)
    setFocusedId(null)
    setDraft('')
    setMessages([])
    void requestReply([])
  }, [player, requestReply])

  // Opener (once)
  const opened = useRef(false)
  useEffect(() => {
    if (opened.current) return
    opened.current = true
    if (messages.length === 0) void requestReply([])
  }, [messages.length, requestReply])

  function send() {
    const text = draft.trim()
    if (!text || phase !== 'idle') return
    player.unlock()
    player.stop()
    setPlayingId(null)
    const message: UserMessage = { id: newId(), role: 'user', text, check: { status: 'checking' } }
    const history = [...messages, message]
    setMessages(history)
    setDraft('')
    void requestReply(history)
  }

  async function transcribe(blob: Blob) {
    setTranscribing(true)
    setError(null)
    try {
      const text = await api.transcribe(blob)
      setDraft((current) => (current.trim() ? `${current.trim()} ${text}` : text))
      input.current?.focus()
    } catch (err) {
      const message =
        err instanceof ApiError && err.status === 422 ? "Didn't catch any speech. Try again." : describeError(err)
      setError({ message })
    } finally {
      setTranscribing(false)
    }
  }

  async function retryCheck(message: UserMessage) {
    const setCheck = (check: UserMessage['check']) =>
      setMessages((current) => current.map((m) => (m.id === message.id ? { ...m, check } : m)))
    setCheck({ status: 'checking' })
    try {
      const correction = await api.correct(message.text, findPartnerLine(messages, message.id), settings.level)
      setCheck({ status: 'done', correction })
    } catch {
      setCheck({ status: 'failed' })
    }
  }

  function changeScenario(scenario: Scenario) {
    setSettings((current) => ({ ...current, scenario }))
    settingsRef.current = { ...settingsRef.current, scenario }
    // Restart if untouched
    if (!messages.some((m) => m.role === 'user')) startConversation()
  }

  const startRecording = useCallback(() => {
    player.unlock()
    player.stop()
    setPlayingId(null)
    setError(null)
  }, [player])

  const showError = useCallback((message: string) => setError({ message }), [])

  const replies = messages.filter((m): m is AiMessage => m.role === 'assistant')
  const latestReply = replies.at(-1) ?? null
  const panelMessage = replies.find((m) => m.id === focusedId) ?? latestReply

  function selectWord(selection: SelectedWord) {
    setFocusedId(selection.messageId)
    setSelected((current) =>
      current?.messageId === selection.messageId && current.key === selection.key ? null : selection,
    )
    setWordsOpen(true)
  }

  function focusMessage(id: string) {
    if (id === panelMessage?.id) return
    setFocusedId(id)
    setSelected(null)
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-ja" lang="ja">
            会話
          </span>
          <span className="brand-name">Hanasu</span>
        </div>
        <div className="topbar-controls">
          <select
            className="scenario-select"
            value={settings.scenario}
            onChange={(e) => changeScenario(e.target.value as Scenario)}
            aria-label="Scenario"
          >
            {Object.entries(SCENARIO_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button type="button" className="ghost-button" onClick={startConversation}>
            New
          </button>
          <button type="button" className="ghost-button words-toggle" onClick={() => setWordsOpen((o) => !o)}>
            Words
          </button>
          <button
            type="button"
            className={`icon-button${settings.voice ? '' : ' off'}`}
            onClick={() => {
              if (settings.voice) player.stop()
              setSettings({ ...settings, voice: !settings.voice })
            }}
            aria-label={settings.voice ? 'Mute replies' : 'Unmute replies'}
            title={settings.voice ? 'Mute replies' : 'Unmute replies'}
          >
            {settings.voice ? '🔊' : '🔇'}
          </button>
          <button
            type="button"
            className="icon-button"
            onClick={() => setShowSettings((open) => !open)}
            aria-label="Settings"
            title="Settings"
          >
            ⚙
          </button>
        </div>
      </header>

      {showSettings && (
        <SettingsPanel settings={settings} onChange={setSettings} onClose={() => setShowSettings(false)} />
      )}

      <main className="conversation">
        <ChatThread
          messages={messages}
          replying={phase === 'replying'}
          showFurigana={settings.furigana}
          panelMessageId={panelMessage?.id ?? null}
          selected={selected}
          playingId={playingId}
          onSelect={selectWord}
          onFocusMessage={focusMessage}
          onPlay={play}
          onRetryCheck={retryCheck}
        />
        {error && (
          <div className="error-banner" role="alert">
            <span>{error.message}</span>
            {error.retry && (
              <button type="button" className="link-button" onClick={error.retry}>
                Retry
              </button>
            )}
            <button type="button" className="icon-button" onClick={() => setError(null)} aria-label="Dismiss">
              ✕
            </button>
          </div>
        )}
        <Composer
          ref={input}
          draft={draft}
          kanaInput={settings.kanaInput}
          deviceId={settings.micDeviceId}
          phase={phase}
          onDraftChange={setDraft}
          onSend={send}
          onRecordStart={startRecording}
          onRecorded={transcribe}
          onError={showError}
        />
      </main>

      <WordPanel
        message={panelMessage}
        isLatest={panelMessage?.id === latestReply?.id}
        selectedKey={selected && selected.messageId === panelMessage?.id ? selected.key : null}
        showFurigana={settings.furigana}
        open={wordsOpen}
        onSelect={(key) => panelMessage && setSelected(key ? { messageId: panelMessage.id, key } : null)}
        onClose={() => setWordsOpen(false)}
      />
    </div>
  )
}
