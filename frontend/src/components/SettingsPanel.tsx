import { useEffect, useState } from 'react'
import { listMicrophones } from '../lib/recorder.ts'
import type { Level, Settings } from '../lib/types.ts'

type Props = {
  settings: Settings
  onChange(settings: Settings): void
  onClose(): void
}

export function SettingsPanel({ settings, onChange, onClose }: Props) {
  const [mics, setMics] = useState<MediaDeviceInfo[]>([])

  useEffect(() => {
    // Microphones
    listMicrophones().then(setMics).catch(() => setMics([]))
  }, [])

  const update = (patch: Partial<Settings>) => onChange({ ...settings, ...patch })

  return (
    <section className="settings" aria-label="Settings">
      <div className="settings-head">
        <h2>Settings</h2>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Close settings">
          ✕
        </button>
      </div>
      <label className="field">
        <span>Level</span>
        <select value={settings.level} onChange={(e) => update({ level: e.target.value as Level })}>
          <option value="beginner">Beginner (N5–N4)</option>
          <option value="intermediate">Intermediate (N3)</option>
        </select>
      </label>
      <label className="field">
        <span>Microphone</span>
        <select value={settings.micDeviceId} onChange={(e) => update({ micDeviceId: e.target.value })}>
          <option value="">System default</option>
          {mics.map((mic, i) => (
            <option key={mic.deviceId || i} value={mic.deviceId}>
              {mic.label || `Microphone ${i + 1}`}
            </option>
          ))}
        </select>
      </label>
      <label className="toggle">
        <input type="checkbox" checked={settings.voice} onChange={(e) => update({ voice: e.target.checked })} />
        <span>Speak replies aloud</span>
      </label>
      <label className="toggle">
        <input
          type="checkbox"
          checked={settings.furigana}
          onChange={(e) => update({ furigana: e.target.checked })}
        />
        <span>Show furigana</span>
      </label>
      <label className="toggle">
        <input
          type="checkbox"
          checked={settings.kanaInput}
          onChange={(e) => update({ kanaInput: e.target.checked })}
        />
        <span>Romaji → kana while typing</span>
      </label>
    </section>
  )
}
