import type { ChatMessage, Settings } from './types.ts'

const SETTINGS_KEY = 'hanasu.settings'
const HISTORY_KEY = 'hanasu.history'

export const DEFAULT_SETTINGS: Settings = {
  level: 'beginner',
  scenario: 'free',
  voice: true,
  furigana: true,
  kanaInput: false,
  micDeviceId: '',
}

// Safe storage
function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

function write(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Memory only
  }
}

export function loadSettings(): Settings {
  return { ...DEFAULT_SETTINGS, ...read<Partial<Settings>>(SETTINGS_KEY) }
}

export function saveSettings(settings: Settings) {
  write(SETTINGS_KEY, settings)
}

export function loadHistory(): ChatMessage[] {
  const messages = read<ChatMessage[]>(HISTORY_KEY) ?? []
  // Interrupted checks
  return messages.map((m) =>
    m.role === 'user' && m.check.status === 'checking' ? { ...m, check: { status: 'failed' } } : m,
  )
}

export function saveHistory(messages: ChatMessage[]) {
  write(HISTORY_KEY, messages)
}
