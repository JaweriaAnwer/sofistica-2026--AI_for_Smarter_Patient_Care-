import { Warning } from '@phosphor-icons/react';

const styles = {
  banner: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    height: 'var(--banner-h)',
    zIndex: 100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    background: 'linear-gradient(90deg, #fff7ed, #fef2f2)',
    borderBottom: '1px solid rgba(217, 119, 6, 0.3)',
    color: '#92400e',
    fontFamily: 'var(--font-ui)',
    fontSize: '0.8rem',
    fontWeight: 600,
    letterSpacing: '0.01em',
    padding: '0 16px',
    textAlign: 'center',
  },
};

/**
 * Persistent, non-dismissible notice required by the hackathon brief.
 * Deliberately has no close button / state — it must always be visible.
 */
export default function SafetyBanner() {
  return (
    <div style={styles.banner} role="alert">
      <Warning size={16} weight="fill" color="#d97706" />
      <span>
        Research and educational prototype only. Not for clinical use. Do not use for diagnosis,
        treatment, triage, or emergency decisions.
      </span>
    </div>
  );
}
