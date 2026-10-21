import type { Token } from './types.ts'

const PARENTHETICAL = /\s*\([^)]*\)\s*/g

// Word identity
export function wordKey(token: Token): string {
  return token.entry_id !== null ? `entry:${token.entry_id}` : `lemma:${token.lemma}`
}

// Vocabulary list
export function listVocabulary(tokens: Token[]): Token[] {
  const seen = new Set<string>()
  return tokens.filter((token) => {
    if (!token.gloss) return false
    const key = wordKey(token)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// Short gloss
export function shortenGloss(gloss: string): string {
  return gloss.replace(PARENTHETICAL, ' ').trim() || gloss
}
