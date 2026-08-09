import { useState } from 'react';
import { WarningOctagon, Warning, Info, CheckCircle, Circle } from '@phosphor-icons/react';

const SEVERITY = {
  critical: { color: 'var(--error)', icon: WarningOctagon, label: 'Critical' },
  warning: { color: 'var(--warning)', icon: Warning, label: 'Warning' },
  info: { color: 'var(--accent)', icon: Info, label: 'Info' },
};

// Distinct orange from the amber "warning" severity color, so the two
// visual signals (severity vs. clinical-finding vs. quality-flag) stay
// legible even when they land on the same card.
const QUALITY_FLAG_ORANGE = '#ea580c';

/**
 * QualityFlagCard — one detected issue from the Data Quality Engine.
 * Left border color encodes what KIND of thing this is (an orange
 * border = a data-quality problem in the record itself; a blue border +
 * badge = a possible genuine clinical finding, not an error) — this is
 * separate from the severity icon/color, which encodes how serious it is.
 */
export default function QualityFlagCard({ flag }) {
  const [reviewed, setReviewed] = useState(false);
  const sev = SEVERITY[flag.severity] || SEVERITY.info;
  const SevIcon = sev.icon;
  const borderColor = flag.is_clinical_finding ? 'var(--accent)' : QUALITY_FLAG_ORANGE;

  return (
    <div
      className="card"
      style={{
        padding: '16px 18px',
        borderLeft: `4px solid ${borderColor}`,
        opacity: reviewed ? 0.6 : 1,
        transition: 'opacity 0.2s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <SevIcon size={18} weight="fill" color={sev.color} style={{ marginTop: 2, flexShrink: 0 }} />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <span className={`chip chip--${flag.severity === 'critical' ? 'error' : flag.severity === 'warning' ? 'warn' : 'ok'}`}>
              {sev.label}
            </span>
            <span
              className="mono"
              style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)', padding: '3px 8px', borderRadius: 999, border: '1px solid var(--card-border)' }}
            >
              {flag.issue_type}
            </span>
            {flag.is_clinical_finding && (
              <span
                className="mono"
                style={{
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  padding: '3px 8px',
                  borderRadius: 999,
                  color: 'var(--accent)',
                  background: 'var(--accent-dim)',
                  border: '1px solid rgba(37,99,235,0.3)',
                }}
              >
                Possible Clinical Finding
              </span>
            )}
          </div>

          <div className="provenance" style={{ marginBottom: 8, display: 'inline-block' }}>
            {flag.table}
            {flag.column ? `.${flag.column}` : ''}
            {flag.affected_row_count ? ` · ${flag.affected_row_count.toLocaleString()} rows` : ''}
          </div>

          <p style={{ margin: '0 0 10px', color: 'var(--text-secondary)', fontSize: '0.87rem', lineHeight: 1.5 }}>
            {flag.description}
          </p>

          {flag.sample_values?.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
              {flag.sample_values.slice(0, 5).map((v, i) => (
                <code
                  key={i}
                  className="mono"
                  style={{
                    fontSize: '0.75rem',
                    padding: '2px 8px',
                    borderRadius: 6,
                    background: 'rgba(15,23,42,0.04)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--text-primary)',
                  }}
                >
                  {v}
                </code>
              ))}
            </div>
          )}

          {flag.suggested_fix && (
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <strong style={{ color: 'var(--text-primary)', flexShrink: 0 }}>Suggested:</strong>
              <span style={{ flex: 1 }}>{flag.suggested_fix}</span>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
            {flag.reversible && (
              <span className="chip chip--ok" style={{ fontSize: '0.65rem' }}>
                Reversible ✓
              </span>
            )}
            <button
              type="button"
              onClick={() => setReviewed((r) => !r)}
              className="btn btn--ghost"
              style={{ marginLeft: 'auto', padding: '5px 10px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              {reviewed ? <CheckCircle size={14} weight="fill" color="var(--accent)" /> : <Circle size={14} />}
              {reviewed ? 'Reviewed' : 'Mark as Reviewed'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
