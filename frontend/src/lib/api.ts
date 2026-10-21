import type { ChatMessage, ChatResponse, Correction, Level, Scenario, Word } from './types.ts'

// Empty = same origin
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request(path: string, init: RequestInit): Promise<Response> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, init)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'Cannot reach the backend. Is it running on port 8000?')
  }
  if (!response.ok) throw new ApiError(response.status, await readDetail(response))
  return response
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    return JSON.stringify(body.detail)
  } catch {
    return `Request failed (${response.status})`
  }
}

function postJson(path: string, body: unknown, signal?: AbortSignal): Promise<Response> {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
}

export type ChatOptions = { level: Level; scenario: Scenario; signal?: AbortSignal }

export const api = {
  async chat(messages: ChatMessage[], { level, scenario, signal }: ChatOptions): Promise<ChatResponse> {
    const history = messages.map((m) => ({ role: m.role, content: m.text }))
    const response = await postJson('/api/chat', { messages: history, level, scenario }, signal)
    return response.json()
  },

  async correct(text: string, partnerText: string | null, level: Level): Promise<Correction> {
    const response = await postJson('/api/correct', { text, partner_text: partnerText, level })
    return response.json()
  },

  async transcribe(audio: Blob, signal?: AbortSignal): Promise<string> {
    const form = new FormData()
    form.append('audio', audio, 'speech')
    const response = await request('/api/stt', { method: 'POST', body: form, signal })
    return (await response.json()).text
  },

  // PCM stream
  speak(text: string, signal?: AbortSignal): Promise<Response> {
    return postJson('/api/tts', { text }, signal)
  },

  async word(entryId: number, signal?: AbortSignal): Promise<Word> {
    const response = await request(`/api/words/${entryId}`, { signal })
    return response.json()
  },
}
