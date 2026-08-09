import { CheckCircle, XCircle } from '@phosphor-icons/react';

function CriteriaColumn({ title, items, color, Icon }) {
  return (
    <div style={{ flex: 1, minWidth: 240 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <Icon size={16} weight="fill" color={color} />
        <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{title}</span>
        <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>({items.length})</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.length === 0 && (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>None specified</div>
        )}
        {items.map((c, i) => (
          <div key={i} className="card" style={{ padding: '12px 14px', borderLeft: `3px solid ${color}` }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: 6 }}>{c.description}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
              {c.table && (
                <span className="mono" style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: 999, border: '1px solid var(--card-border)', color: 'var(--text-secondary)' }}>
                  {c.table}
                </span>
              )}
              {c.condition && (
                <code className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>{c.condition}</code>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * CriteriaCards — renders the LLM's inclusion_criteria / exclusion_criteria
 * arrays as two side-by-side columns, so the cohort definition's logic is
 * visible and auditable rather than hidden inside raw SQL.
 */
export default function CriteriaCards({ inclusionCriteria = [], exclusionCriteria = [] }) {
  return (
    <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
      <CriteriaColumn title="Inclusion Criteria" items={inclusionCriteria} color="#16a34a" Icon={CheckCircle} />
      <CriteriaColumn title="Exclusion Criteria" items={exclusionCriteria} color="var(--error)" Icon={XCircle} />
    </div>
  );
}
