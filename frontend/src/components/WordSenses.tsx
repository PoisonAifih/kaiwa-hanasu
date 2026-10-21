import { useEffect, useState } from 'react'
import { api, ApiError } from '../lib/api.ts'
import type { Word } from '../lib/types.ts'

type Load = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; word: Word }

// Word senses
export function WordSenses({ entryId }: { entryId: number }) {
  const [load, setLoad] = useState<Load>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    setLoad({ status: 'loading' })
    api
      .word(entryId, controller.signal)
      .then((word) => setLoad({ status: 'ready', word }))
      .catch((error) => {
        if (controller.signal.aborted) return
        setLoad({ status: 'error', message: error instanceof ApiError ? error.message : 'Failed to load' })
      })
    return () => controller.abort()
  }, [entryId])

  if (load.status === 'loading') return <p className="senses-status muted">Loading…</p>
  if (load.status === 'error') return <p className="senses-status error-text">{load.message}</p>
  const { word } = load
  return (
    <div className="word-senses">
      <div className="word-forms" lang="ja">
        {[...word.kanji, ...word.readings].join('・')}
        {word.common && <span className="badge badge-common">Common</span>}
      </div>
      <ol className="senses">
        {word.senses.map((sense, i) => (
          <li key={i}>
            {sense.parts_of_speech.length > 0 && <div className="sense-pos">{sense.parts_of_speech.join(' · ')}</div>}
            <div className="sense-glosses">{sense.glosses.join('; ')}</div>
            {(sense.misc.length > 0 || sense.info.length > 0) && (
              <div className="sense-notes">{[...sense.misc, ...sense.info].join(' · ')}</div>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}
