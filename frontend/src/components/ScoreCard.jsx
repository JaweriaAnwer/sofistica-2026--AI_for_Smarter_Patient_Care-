import SpotlightCard from './SpotlightCard';
import AnimatedCounter from './AnimatedCounter';

/**
 * ScoreCard — one of the four top-row summary cards on the Data Quality
 * page (Total / Critical / Warnings / Info). `accent` drives both the
 * spotlight glow color and the number color.
 */
export default function ScoreCard({ label, value, accent = 'var(--accent)', icon: Icon }) {
  return (
    <SpotlightCard accent={accent} style={{ padding: '18px 20px', flex: 1, minWidth: 140 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        {Icon && <Icon size={16} color={accent} weight="fill" />}
        <span
          className="mono"
          style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}
        >
          {label}
        </span>
      </div>
      <AnimatedCounter value={value} style={{ fontSize: '1.9rem', fontWeight: 800, color: accent }} />
    </SpotlightCard>
  );
}
