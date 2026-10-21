// Silence gate
const MIN_DURATION_MS = 500
const MIN_PEAK_RMS = 0.015
const ANALYSER_SIZE = 1024

export type Recording = { blob: Blob; durationMs: number }

export class TooQuietError extends Error {}

// Recorder
export class Recorder {
  private readonly chunks: Blob[] = []
  private readonly startedAt = performance.now()
  private peak = 0
  private frame = 0

  private constructor(
    private readonly stream: MediaStream,
    private readonly recorder: MediaRecorder,
    private readonly context: AudioContext,
    private readonly analyser: AnalyserNode,
  ) {
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.chunks.push(event.data)
    }
    recorder.start()
    this.trackPeak()
  }

  static async start(deviceId: string): Promise<Recorder> {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: deviceId ? { deviceId: { exact: deviceId } } : true,
    })
    const context = new AudioContext()
    await context.resume().catch(() => {})
    const analyser = context.createAnalyser()
    analyser.fftSize = ANALYSER_SIZE
    context.createMediaStreamSource(stream).connect(analyser)
    // Browser default format
    return new Recorder(stream, new MediaRecorder(stream), context, analyser)
  }

  stop(): Promise<Recording> {
    return new Promise((resolve, reject) => {
      this.recorder.onstop = () => {
        const durationMs = performance.now() - this.startedAt
        const peak = this.peak
        // Suspended context: length only
        const measured = this.context.state === 'running'
        this.release()
        if (durationMs < MIN_DURATION_MS || (measured && peak < MIN_PEAK_RMS)) {
          reject(new TooQuietError("Didn't catch that. Hold the button while you speak."))
          return
        }
        resolve({ blob: new Blob(this.chunks, { type: this.recorder.mimeType }), durationMs })
      }
      this.recorder.stop()
    })
  }

  cancel() {
    this.recorder.onstop = null
    if (this.recorder.state !== 'inactive') this.recorder.stop()
    this.release()
  }

  private trackPeak() {
    const samples = new Float32Array(this.analyser.fftSize)
    const tick = () => {
      this.analyser.getFloatTimeDomainData(samples)
      let sum = 0
      for (const sample of samples) sum += sample * sample
      this.peak = Math.max(this.peak, Math.sqrt(sum / samples.length))
      this.frame = requestAnimationFrame(tick)
    }
    this.frame = requestAnimationFrame(tick)
  }

  private release() {
    cancelAnimationFrame(this.frame)
    for (const track of this.stream.getTracks()) track.stop()
    if (this.context.state !== 'closed') void this.context.close()
  }
}

export async function listMicrophones(): Promise<MediaDeviceInfo[]> {
  if (!navigator.mediaDevices?.enumerateDevices) return []
  const devices = await navigator.mediaDevices.enumerateDevices()
  return devices.filter((device) => device.kind === 'audioinput')
}
