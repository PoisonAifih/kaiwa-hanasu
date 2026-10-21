export type Level = 'beginner' | 'intermediate'
export type Scenario = 'free' | 'self_intro' | 'cafe' | 'weekend'
export type IssueCategory = 'grammar' | 'particle' | 'word_choice' | 'politeness' | 'naturalness'

export type Issue = {
  category: IssueCategory
  original_span: string
  suggestion: string
  note: string
  start: number | null
  end: number | null
}

export type Correction = {
  ok: boolean
  original: string
  corrected: string
  issues: Issue[]
}

export type FuriganaSegment = { text: string; ruby: string | null }

export type Token = {
  surface: string
  start: number
  end: number
  reading: string
  lemma: string
  pos: string
  gloss: string | null
  entry_id: number | null
  furigana: FuriganaSegment[]
}

export type ChatResponse = {
  reply: string
  translation: string | null
  correction: Correction | null
  tokens: Token[]
}

export type Sense = {
  parts_of_speech: string[]
  glosses: string[]
  misc: string[]
  info: string[]
}

export type Word = {
  id: number
  kanji: string[]
  readings: string[]
  common: boolean
  senses: Sense[]
}

export type CorrectionState =
  | { status: 'checking' }
  | { status: 'failed' }
  | { status: 'done'; correction: Correction }

export type UserMessage = {
  id: string
  role: 'user'
  text: string
  check: CorrectionState
}

export type AiMessage = {
  id: string
  role: 'assistant'
  text: string
  // Optional (older replies)
  translation?: string | null
  tokens: Token[]
}

export type ChatMessage = UserMessage | AiMessage

export type Settings = {
  level: Level
  scenario: Scenario
  voice: boolean
  furigana: boolean
  kanaInput: boolean
  micDeviceId: string
}
