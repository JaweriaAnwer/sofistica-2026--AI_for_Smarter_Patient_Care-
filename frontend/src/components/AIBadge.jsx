import { Sparkle } from '@phosphor-icons/react';

/**
 * AIBadge — small reusable tag marking content that came from an LLM
 * (e.g. the Cohort Builder's natural-language-to-SQL translation).
 * Never use this on rule-based output (like Data Quality Engine flags) —
 * it should only appear where an AI model actually generated the content,
 * per the challenge brief's requirement to make AI-generated content
 * visually distinguishable from source data.
 */
export default function AIBadge({ style, label = 'AI Generated' }) {
  return (
    <span
      className="mono"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontSize: '0.68rem',
        fontWeight: 600,
        letterSpacing: '0.03em',
        textTransform: 'uppercase',
        padding: '3px 10px',
        borderRadius: 999,
        color: 'var(--accent)',
        background: 'var(--accent-dim)',
        border: '1px solid rgba(37, 99, 235, 0.35)',
        boxShadow: '0 0 10px -2px var(--accent-glow)',
        ...style,
      }}
    >
      <Sparkle size={12} weight="fill" />
      {label}
    </span>
  );
}
