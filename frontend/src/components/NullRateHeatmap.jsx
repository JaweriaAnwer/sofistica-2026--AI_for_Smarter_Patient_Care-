const MAX_COLS_SHOWN = 10;

function cellColor(rate) {
  // 0% null -> near-white, 100% null -> solid red. Blue-ish theme keeps
  // "healthy" cells neutral so the eye is drawn only to problem cells.
  if (rate <= 0.02) return 'rgba(37, 99, 235, 0.08)';
  const alpha = 0.15 + Math.min(rate, 1) * 0.75;
  return `rgba(220, 38, 38, ${alpha.toFixed(2)})`;
}

/**
 * NullRateHeatmap — one row per table, one cell per column (columns
 * sorted worst-first, capped at MAX_COLS_SHOWN with a "+N more" note
 * since some MIMIC-IV tables have 20+ columns). Cell color intensity
 * encodes null rate; hover a cell for the exact percentage.
 */
export default function NullRateHeatmap({ tables }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {tables.map((t) => {
        const entries = Object.entries(t.null_rates || {}).sort((a, b) => b[1] - a[1]);
        const shown = entries.slice(0, MAX_COLS_SHOWN);
        const extra = entries.length - shown.length;
        return (
          <div key={t.table} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              className="mono"
              style={{ width: 130, flexShrink: 0, fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
              title={t.table}
            >
              {t.table}
            </div>
            <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', flex: 1 }}>
              {shown.map(([col, rate]) => (
                <div
                  key={col}
                  title={`${col}: ${(rate * 100).toFixed(1)}% null`}
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 5,
                    background: cellColor(rate),
                    border: '1px solid rgba(15,23,42,0.06)',
                    cursor: 'help',
                  }}
                />
              ))}
              {extra > 0 && (
                <span
                  className="mono"
                  style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', paddingLeft: 4 }}
                >
                  +{extra} more
                </span>
              )}
            </div>
          </div>
        );
      })}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, paddingLeft: 140 }}>
        <span className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)' }}>0%</span>
        <div style={{ display: 'flex', gap: 2 }}>
          {[0, 0.15, 0.3, 0.5, 0.75, 1].map((r) => (
            <div key={r} style={{ width: 16, height: 10, background: cellColor(r), borderRadius: 2 }} />
          ))}
        </div>
        <span className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)' }}>100% null</span>
      </div>
    </div>
  );
}
