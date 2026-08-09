import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, Legend, Tooltip as RTooltip, ResponsiveContainer } from 'recharts';
import { MagnifyingGlassPlus, Sparkle, Info, WarningOctagon, CaretUp, CaretDown, Users } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import SpotlightCard from '../components/SpotlightCard';
import AnimatedCounter from '../components/AnimatedCounter';
import AIBadge from '../components/AIBadge';
import SQLEditor from '../components/SQLEditor';
import CriteriaCards from '../components/CriteriaCards';
import ProvenanceTooltip from '../components/ProvenanceTooltip';
import StatBarChart from '../components/StatBarChart';
import { API_BASE_URL, apiGet, apiPost } from '../lib/api';

const GENDER_COLORS = { F: '#2563eb', M: '#93c5fd', Other: '#94a3b8' };

export default function CohortBuilder() {
  const [connectionOk, setConnectionOk] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [columnTableMap, setColumnTableMap] = useState({});

  const [nlInput, setNlInput] = useState('');
  const [generating, setGenerating] = useState(false);
  const [running, setRunning] = useState(false);

  const [sql, setSql] = useState('');
  const [criteria, setCriteria] = useState(null); // { inclusion_criteria, exclusion_criteria, tables_used, explanation }
  const [results, setResults] = useState(null); // execute_cohort_query() shape
  const [abstain, setAbstain] = useState(null); // { reason } | null
  const [error, setError] = useState(null);

  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  // ── Initial data: templates + schema (for provenance table lookup) ──
  useEffect(() => {
    apiGet('/api/health')
      .then(() => setConnectionOk(true))
      .catch(() => setConnectionOk(false));

    apiGet('/api/cohort/templates')
      .then((res) => setTemplates(res.templates || []))
      .catch(() => {});

    apiGet('/api/schema')
      .then((res) => {
        const map = {};
        for (const t of res.tables || []) {
          for (const col of t.columns || []) {
            if (!(col.name in map)) map[col.name] = t.name; // first table wins
          }
        }
        setColumnTableMap(map);
      })
      .catch(() => {});
  }, []);

  function resetResultState() {
    setAbstain(null);
    setError(null);
  }

  async function handleGenerate() {
    if (!nlInput.trim()) return;
    resetResultState();
    setGenerating(true);
    setResults(null);
    setCriteria(null);
    setSql('');
    try {
      const res = await apiPost('/api/cohort/query', { text: nlInput.trim() });
      if (res.abstain) {
        setAbstain({ reason: res.reason });
        if (res.sql) setSql(res.sql);
        return;
      }
      setSql(res.sql || '');
      setCriteria({
        inclusion_criteria: res.inclusion_criteria || [],
        exclusion_criteria: res.exclusion_criteria || [],
        tables_used: res.tables_used || [],
        explanation: res.explanation || '',
      });
      setResults(res.results);
    } catch (e) {
      setError(e.message || 'Something went wrong generating this query.');
    } finally {
      setGenerating(false);
    }
  }

  async function handleRun(editedSql) {
    resetResultState();
    setRunning(true);
    try {
      const res = await apiPost('/api/cohort/execute', { sql: editedSql });
      setSql(res.sql);
      setResults(res.results);
      // Editing SQL directly bypasses the LLM, so drop the (now possibly
      // stale) criteria cards rather than show logic that no longer
      // matches the query that actually ran.
      setCriteria((prev) => (prev ? { ...prev, tables_used: res.tables_used || prev.tables_used } : prev));
    } catch (e) {
      setError(e.message || 'Query execution failed.');
    } finally {
      setRunning(false);
    }
  }

  function handleTemplateClick(t) {
    setNlInput(t.natural_language);
  }

  const genderData = useMemo(() => {
    const counts = results?.demographics?.gender_counts || {};
    return Object.entries(counts).map(([gender, count]) => ({ gender, count }));
  }, [results]);

  const tableRows = useMemo(() => {
    const rows = (results?.sample_rows || []).slice(0, 20);
    if (!sortKey) return rows;
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') return sortDir === 'asc' ? av - bv : bv - av;
      return sortDir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [results, sortKey, sortDir]);

  function toggleSort(col) {
    if (sortKey === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col);
      setSortDir('asc');
    }
  }

  const busy = generating || running;

  return (
    <div className="slide-up">
      <PageHeader
        eyebrow="TRACK 2 · COHORT DEFINITION"
        title="Cohort Builder"
        description="Turn a plain-language research question into a structured, patient-grouped cohort query with visible inclusion and exclusion logic — every filter traces back to a source table and field."
      />

      {connectionOk === false && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(220,38,38,0.35)', marginBottom: 20 }}>
          <span className="chip chip--error">Backend unreachable</span>
          <p style={{ color: 'var(--text-secondary)', marginTop: 10, marginBottom: 0 }}>
            No response from <code className="mono">{API_BASE_URL}</code>. Make sure the FastAPI server is
            running (<code className="mono">uvicorn backend.main:app --reload</code>).
          </p>
        </div>
      )}

      {/* B3.1 — NL input bar + template chips */}
      <SpotlightCard style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <MagnifyingGlassPlus size={18} color="var(--text-tertiary)" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              value={nlInput}
              onChange={(e) => setNlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !busy && handleGenerate()}
              placeholder="e.g. Adults over 65 with at least one ICU stay"
              style={{
                width: '100%',
                padding: '13px 14px 13px 42px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--card-border)',
                background: '#fff',
                fontSize: '0.9rem',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
          </div>
          <button type="button" className="btn btn--primary" style={{ padding: '0 20px', display: 'inline-flex', alignItems: 'center', gap: 7 }} onClick={handleGenerate} disabled={busy || !nlInput.trim()}>
            <Sparkle size={15} weight="fill" />
            {generating ? 'Generating…' : 'Generate Query'}
          </button>
        </div>

        {templates.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => handleTemplateClick(t)}
                className="mono"
                style={{
                  fontSize: '0.72rem',
                  padding: '6px 12px',
                  borderRadius: 999,
                  border: '1px solid var(--card-border)',
                  background: nlInput === t.natural_language ? 'var(--accent-dim)' : '#fff',
                  color: nlInput === t.natural_language ? 'var(--accent)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                title={t.description}
              >
                {t.name}
              </button>
            ))}
          </div>
        )}
      </SpotlightCard>

      {generating && <LoadingState label="Translating your question with the LLM…" />}

      {/* B3.6 — abstention */}
      {!generating && abstain && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(217,119,6,0.35)', marginBottom: 20, display: 'flex', gap: 12 }}>
          <Info size={20} color="var(--warning)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>This question can't be answered from the available structured data.</strong>
            <p style={{ color: 'var(--text-secondary)', margin: '6px 0 0', fontSize: '0.87rem' }}>
              Reason: {abstain.reason}
            </p>
          </div>
        </div>
      )}

      {/* B3.6 — error */}
      {!generating && error && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(220,38,38,0.35)', marginBottom: 20, display: 'flex', gap: 12 }}>
          <WarningOctagon size={20} color="var(--error)" weight="fill" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>Something went wrong.</strong>
            <p style={{ color: 'var(--text-secondary)', margin: '6px 0 0', fontSize: '0.87rem' }}>{error}</p>
          </div>
        </div>
      )}

      {/* SQL editor + criteria + results */}
      {!generating && sql && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <AIBadge />
            </div>
            <SQLEditor sql={sql} onRun={handleRun} running={running} />
          </div>

          {criteria && (criteria.inclusion_criteria.length > 0 || criteria.exclusion_criteria.length > 0) && (
            <SpotlightCard style={{ padding: 20 }}>
              <CriteriaCards inclusionCriteria={criteria.inclusion_criteria} exclusionCriteria={criteria.exclusion_criteria} />
            </SpotlightCard>
          )}

          {/* B3.4 — results panel */}
          {results && (
            <>
              <SpotlightCard style={{ padding: 22 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Users size={22} color="var(--accent)" />
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Matching cohort
                    </div>
                    <AnimatedCounter value={results.patient_count} style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--accent)' }} />
                  </div>
                  {results.execution_time_ms != null && (
                    <span className="mono" style={{ marginLeft: 'auto', fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>
                      {results.execution_time_ms}ms
                    </span>
                  )}
                </div>

                {results.patient_count === 0 && (
                  <p style={{ marginTop: 14, marginBottom: 0, color: 'var(--text-secondary)', fontSize: '0.87rem' }}>
                    0 patients match this cohort definition in the 100-patient demo sample. The criteria above are
                    still valid — this sample may simply be too small for this combination.
                  </p>
                )}
              </SpotlightCard>

              {results.patient_count > 0 && (
                <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
                  <SpotlightCard style={{ padding: 22, flex: '1 1 320px' }}>
                    <strong style={{ fontSize: '0.85rem' }}>Age distribution</strong>
                    <div style={{ marginTop: 12 }}>
                      <StatBarChart
                        data={results.demographics?.age_distribution || []}
                        dataKey="count"
                        xKey="range"
                        unitLabel="patients"
                        gradientId="ageHistFill"
                        height={200}
                      />
                    </div>
                  </SpotlightCard>

                  <SpotlightCard style={{ padding: 22, flex: '1 1 260px' }}>
                    <strong style={{ fontSize: '0.85rem' }}>Gender</strong>
                    <div style={{ width: '100%', height: 200, marginTop: 4 }}>
                      <ResponsiveContainer>
                        <PieChart>
                          <Pie data={genderData} dataKey="count" nameKey="gender" innerRadius={44} outerRadius={72} paddingAngle={3}>
                            {genderData.map((d, i) => (
                              <Cell key={i} fill={GENDER_COLORS[d.gender] || '#94a3b8'} />
                            ))}
                          </Pie>
                          <Legend iconSize={9} wrapperStyle={{ fontSize: '0.75rem' }} />
                          <RTooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </SpotlightCard>
                </div>
              )}

              {tableRows.length > 0 && (
                <SpotlightCard style={{ padding: 0, overflow: 'auto' }}>
                  <div style={{ padding: '16px 20px 4px' }}>
                    <strong style={{ fontSize: '0.85rem' }}>
                      Results ({tableRows.length} of {results.total_rows} rows shown)
                    </strong>
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr>
                        {(results.columns || []).map((col) => (
                          <th
                            key={col}
                            onClick={() => toggleSort(col)}
                            className="mono"
                            style={{
                              textAlign: 'left',
                              padding: '10px 16px',
                              borderBottom: '1px solid var(--card-border)',
                              cursor: 'pointer',
                              userSelect: 'none',
                              color: 'var(--text-secondary)',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                              {col}
                              {sortKey === col && (sortDir === 'asc' ? <CaretUp size={11} /> : <CaretDown size={11} />)}
                            </span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {tableRows.map((row, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--card-border)' }}>
                          {(results.columns || []).map((col) => (
                            <td key={col} className="mono" style={{ padding: '9px 16px', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                              <ProvenanceTooltip table={columnTableMap[col] || criteria?.tables_used?.[0] || '?'} column={col} subjectId={row.subject_id}>
                                {row[col] === null || row[col] === undefined ? <span style={{ color: 'var(--text-tertiary)' }}>—</span> : String(row[col])}
                              </ProvenanceTooltip>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </SpotlightCard>
              )}
            </>
          )}
        </motion.div>
      )}
    </div>
  );
}
