import { api } from './api.ts'
import { PcmDecoder, readSampleRate } from './pcm.ts'

// First-sentence split
const MIN_FIRST_SENTENCE = 8
const SENTENCE_END = /[。！？!?]/g
// Scheduling
const START_DELAY_SECONDS = 0.08
const MIN_BATCH_SECONDS = 0.12

export function splitForSpeech(text: string): string[] {
  for (const match of text.matchAll(SENTENCE_END)) {
    const end = match.index + 1
    if (end < MIN_FIRST_SENTENCE) continue
    const rest = text.slice(end).trim()
    return rest ? [text.slice(0, end), rest] : [text]
  }
  return [text]
}

function concat(parts: Float32Array<ArrayBuffer>[], length: number): Float32Array<ArrayBuffer> {
  const joined = new Float32Array(length)
  let offset = 0
  for (const part of parts) {
    joined.set(part, offset)
    offset += part.length
  }
  return joined
}

// Player
export class SpeechPlayer {
  private context: AudioContext | null = null
  private controller: AbortController | null = null
  private readonly sources = new Set<AudioBufferSourceNode>()
  private endTime = 0

  // User gesture
  unlock() {
    this.context ??= new AudioContext()
    if (this.context.state === 'suspended') void this.context.resume()
  }

  get canAutoplay(): boolean {
    return this.context?.state === 'running'
  }

  async speak(text: string): Promise<void> {
    this.stop()
    this.unlock()
    const context = this.context!
    const controller = new AbortController()
    this.controller = controller
    this.endTime = 0
    const responses = splitForSpeech(text).map((part) => api.speak(part, controller.signal))
    for (const response of responses) response.catch(() => {})
    try {
      for (const response of responses) await this.stream(context, await response, controller.signal)
      await this.untilSilent(context, controller.signal)
    } catch (error) {
      if (controller.signal.aborted) return
      throw error
    }
  }

  stop() {
    this.controller?.abort()
    this.controller = null
    for (const source of this.sources) source.stop()
    this.sources.clear()
  }

  private async stream(context: AudioContext, response: Response, signal: AbortSignal) {
    const rate = readSampleRate(response.headers.get('content-type'))
    const decoder = new PcmDecoder()
    const reader = response.body!.getReader()
    let batch: Float32Array<ArrayBuffer>[] = []
    let batchLength = 0
    for (;;) {
      const { done, value } = await reader.read()
      if (signal.aborted) return
      if (value) {
        const samples = decoder.decode(value)
        batch.push(samples)
        batchLength += samples.length
      }
      if (batchLength > 0 && (done || batchLength >= rate * MIN_BATCH_SECONDS)) {
        this.play(context, concat(batch, batchLength), rate)
        batch = []
        batchLength = 0
      }
      if (done) return
    }
  }

  private play(context: AudioContext, samples: Float32Array<ArrayBuffer>, rate: number) {
    const buffer = context.createBuffer(1, samples.length, rate)
    buffer.copyToChannel(samples, 0)
    const source = context.createBufferSource()
    source.buffer = buffer
    source.connect(context.destination)
    source.onended = () => this.sources.delete(source)
    const startAt = Math.max(this.endTime, context.currentTime + START_DELAY_SECONDS)
    source.start(startAt)
    this.sources.add(source)
    this.endTime = startAt + buffer.duration
  }

  private untilSilent(context: AudioContext, signal: AbortSignal): Promise<void> {
    const left = Math.max(0, this.endTime - context.currentTime)
    return new Promise((resolve) => {
      const timer = window.setTimeout(resolve, left * 1000)
      signal.addEventListener(
        'abort',
        () => {
          window.clearTimeout(timer)
          resolve()
        },
        { once: true },
      )
    })
  }
}
