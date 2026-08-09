import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiGet } from '../lib/api';

/**
 * ProvenanceTooltip — wraps a value and shows where it came from on
 * hover. Two modes:
 *  - rowId provided: fetches GET /api/coverage/provenance and shows the
 *    exact source row (table, column, sqlite rowid, raw value).
 *  - rowId omitted (e.g. a cohort-query result cell, which comes from a
 *    multi-table JOIN with no single source rowid): shows table.column
 *    plus the patient it belongs to, WITHOUT claiming a row_id we don't
 *    actually have. Never fabricate a row number.
 */
export default function ProvenanceTooltip({ table, column, rowId, subjectId, children }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleEnter() {
    setOpen(true);
    if (rowId != null && table && column && !detail && !loading) {
      setLoading(true);
      apiGet(`/api/coverage/provenance?table=${encodeURIComponent(table)}&column=${encodeURIComponent(column)}&row_id=${rowId}`)
        .then(setDetail)
        .catch(() => setDetail({ error: 'unavailable' }))
        .finally(() => setLoading(false));
    }
  }

  return (
    <span style={{ position: 'relative', display: 'inline-block' }} onMouseEnter={handleEnter} onMouseLeave={() => setOpen(false)}>
      <span style={{ borderBottom: '1px dotted var(--text-tertiary)', cursor: 'help' }}>{children}</span>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.97 }}
            transition={{ duration: 0.14 }}
            style={{
              position: 'absolute',
              bottom: '125%',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 50,
              minWidth: 190,
              padding: '9px 12px',
              borderRadius: 8,
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '0.72rem',
              boxShadow: '0 12px 28px -8px rgba(15,23,42,0.4)',
              pointerEvents: 'none',
            }}
            className="mono"
          >
            <div style={{ color: '#60a5fa', fontWeight: 600, marginBottom: 3 }}>
              Source: {table}.{column}
            </div>
            {rowId != null ? (
              loading ? (
                <div style={{ color: '#94a3b8' }}>Looking up row…</div>
              ) : detail?.error ? (
                <div style={{ color: '#f87171' }}>Row lookup unavailable</div>
              ) : (
                <div style={{ color: '#94a3b8' }}>Row: {detail?.row_id ?? rowId}</div>
              )
            ) : (
              <div style={{ color: '#94a3b8' }}>{subjectId != null ? `Patient ${subjectId}` : 'From joined cohort query'}</div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}
