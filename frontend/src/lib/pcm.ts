const DEFAULT_SAMPLE_RATE = 24000
const INT16_RANGE = 32768

// Sample rate
export function readSampleRate(contentType: string | null): number {
  const rate = Number(/rate=(\d+)/.exec(contentType ?? '')?.[1])
  return rate > 0 ? rate : DEFAULT_SAMPLE_RATE
}

// Int16 -> float
export class PcmDecoder {
  private carry: number | null = null

  decode(bytes: Uint8Array): Float32Array<ArrayBuffer> {
    const joined = this.carry === null ? bytes : prepend(this.carry, bytes)
    const usable = joined.length - (joined.length % 2)
    this.carry = usable < joined.length ? joined[usable]! : null
    const view = new DataView(joined.buffer, joined.byteOffset, usable)
    const samples = new Float32Array(usable / 2)
    for (let i = 0; i < samples.length; i += 1) {
      samples[i] = view.getInt16(i * 2, true) / INT16_RANGE
    }
    return samples
  }
}

function prepend(first: number, rest: Uint8Array): Uint8Array {
  const joined = new Uint8Array(rest.length + 1)
  joined[0] = first
  joined.set(rest, 1)
  return joined
}
