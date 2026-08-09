import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, CaretDown, WarningOctagon, Warning, Info, DownloadSimple } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import { SkeletonScoreCards, SkeletonRows } from '../components/Skeleton';
import ScoreCard from '../components/ScoreCard';
import QualityFlagCard from '../components/QualityFlagCard';
import { API_BASE_URL, apiGet } from '../lib/api';

const CATEGORIES = ['MISSING', 'DUPLICATE', 'IMPLAUSIBLE', 'TEMPORAL', 'UNIT_INCONSISTENCY', 'ORPHAN_FK', 'CODING_PATTERN'];

function download(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function flagsToCSV(flags) {
  const cols = ['id', 'table', 'column', 'issue_type', 'severity', 'description', 'affected_row_count', 'is_clinical_finding', 'reversible', 'suggested_fix'];
  const escape = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const rows = flags.map((f) => cols.map((c) => escape(f[c])).join(','));
  return [cols.join(','), ...rows].join('\n');
}

export default function DataQuality() {
  const [status, setStatus] = useState('loading');
  const [summary, setSummary] = useState(null);
  const [flags, setFlags] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [openTable, setOpenTable] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    Promise.all([apiGet('/api/quality/summary'), apiGet('/api/quality/scan')])
      .then(([summaryRes, scanRes]) => {
        if (cancelled) return;
        setSummary(summaryRes);
        setFlags(scanRes.flags || []);
        setStatus('ready');
      })
      .catch(() => !cancelled && setStatus('error'));
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredFlags = useMemo(() => {
    return flags.filter(
      (f) => (severityFilter === 'all' || f.severity === severityFilter) && (categoryFilter === 'all' || f.issue_type === categoryFilter)
    );
  }, [flags, severityFilter, categoryFilter]);

  const byTable = useMemo(() => {
    const groups = {};
    for (const f of filteredFlags) {
      (groups[f.table] ||= []).push(f);
    }
    return Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
  }, [filteredFlags]);

  return (
    <div className="slide-up">
      <PageHeader
        eyebrow="TRACK 2 · DATA QUALITY"
        title="Data Quality Inspector"
        description="Surface missing, duplicated, inconsistent, implausible, or temporally misaligned records. Every flag is a documented rule, not a silent fix — nothing here deletes or overwrites the source data."
      />

      {status === 'loading' && (
        <>
          <SkeletonScoreCards count={4} />
          <SkeletonRows rows={5} />
        </>
      )}

      {status === 'error' && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(220,38,38,0.35)' }}>
          <span className="chip chip--error">Backend unreachable</span>
          <p style={{ color: 'var(--text-secondary)', marginTop: 10, marginBottom: 0 }}>
            No response from <code className="mono">{API_BASE_URL}</code>. Make sure the FastAPI server is
            running (<code className="mono">uvicorn backend.main:app --reload</code>).
          </p>
        </div>
      )}

      {status === 'ready' && summary && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          {/* B2.1 — Summary scorecards */}
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 24 }}>
            <ScoreCard label="Total Issues" value={summary.total_flags} accent="var(--text-primary)" icon={Database} />
            <ScoreCard label="Critical" value={summary.by_severity.critical} accent="var(--error)" icon={WarningOctagon} />
            <ScoreCard label="Warnings" value={summary.by_severity.warning} accent="var(--warning)" icon={Warning} />
            <ScoreCard label="Info" value={summary.by_severity.info} accent="var(--accent)" icon={Info} />
          </div>

          {/* Filter bar + export */}
          <div
            className="card"
            style={{ padding: '14px 18px', display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', marginBottom: 20 }}
          >
            <FilterSelect label="Severity" value={severityFilter} onChange={setSeverityFilter} options={['all', 'critical', 'warning', 'info']} />
            <FilterSelect label="Category" value={categoryFilter} onChange={setCategoryFilter} options={['all', ...CATEGORIES]} />
            <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
              {filteredFlags.length} of {flags.length} flags shown
            </span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <button
                type="button"
                className="btn btn--ghost"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.78rem' }}
                onClick={() => download('cliniq-quality-report.json', JSON.stringify(filteredFlags, null, 2), 'application/json')}
              >
                <DownloadSimple size={14} /> Export JSON
              </button>
              <button
                type="button"
                className="btn btn--ghost"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.78rem' }}
                onClick={() => download('cliniq-quality-report.csv', flagsToCSV(filteredFlags), 'text/csv')}
              >
                <DownloadSimple size={14} /> Export CSV
              </button>
            </div>
          </div>

          {/* B2.2 — Table-level accordion breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {byTable.length === 0 && (
              <div className="card" style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)' }}>
                No flags match the current filters.
              </div>
            )}
            {byTable.map(([table, tableFlags]) => {
              const isOpen = openTable === table;
              return (
                <div key={table} className="card" style={{ overflow: 'hidden' }}>
                  <button
                    type="button"
                    onClick={() => setOpenTable(isOpen ? null : table)}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '14px 18px',
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <span className="mono" style={{ fontWeight: 700 }}>
                      {table}
                    </span>
                    <span className="chip chip--warn">{tableFlags.length} issue{tableFlags.length === 1 ? '' : 's'}</span>
                    <motion.span
                      animate={{ rotate: isOpen ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                      style={{ marginLeft: 'auto', display: 'flex' }}
                    >
                      <CaretDown size={16} color="var(--text-tertiary)" />
                    </motion.span>
                  </button>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '0 18px 18px' }}>
                          {tableFlags.map((f) => (
                            <QualityFlagCard key={f.id} flag={f} />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mono"
        style={{
          padding: '5px 8px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--card-border)',
          background: '#fff',
          color: 'var(--text-primary)',
          fontSize: '0.78rem',
        }}
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o === 'all' ? 'All' : o}
          </option>
        ))}
      </select>
    </label>
  );
}
