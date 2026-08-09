import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ChartDonut, Table, Users, UserCircle, CheckCircle, XCircle } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import { SkeletonChartCard } from '../components/Skeleton';
import SpotlightCard from '../components/SpotlightCard';
import StatBarChart from '../components/StatBarChart';
import NullRateHeatmap from '../components/NullRateHeatmap';
import { API_BASE_URL, apiGet } from '../lib/api';

export default function CoverageExplorer() {
  const [status, setStatus] = useState('loading');
  const [tables, setTables] = useState([]);

  // Patient drill-down (B3.7)
  const [allPatients, setAllPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientCoverage, setPatientCoverage] = useState(null);
  const [patientStatus, setPatientStatus] = useState('idle');

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    apiGet('/api/coverage/summary')
      .then((res) => {
        if (cancelled) return;
        setTables(res.tables || []);
        setStatus('ready');
      })
      .catch(() => !cancelled && setStatus('error'));
    return () => {
      cancelled = true;
    };
  }, []);

  // Load the first patient's coverage on mount (also populates the
  // dropdown's option list via all_patients in the same response).
  useEffect(() => {
    let cancelled = false;
    setPatientStatus('loading');
    apiGet('/api/coverage/patient/1')
      .then((res) => {
        if (cancelled) return;
        setAllPatients(res.all_patients || []);
        setSelectedPatient(res.subject_id);
        setPatientCoverage(res);
        setPatientStatus('ready');
      })
      .catch(() => !cancelled && setPatientStatus('error'));
    return () => {
      cancelled = true;
    };
  }, []);

  function handlePatientChange(subjectId) {
    setSelectedPatient(subjectId);
    setPatientStatus('loading');
    apiGet(`/api/coverage/patient/${subjectId}`)
      .then((res) => {
        setPatientCoverage(res);
        setPatientStatus('ready');
      })
      .catch(() => setPatientStatus('error'));
  }

  const patientFreqData = useMemo(
    () =>
      (patientCoverage?.coverage || [])
        .filter((c) => c.row_count > 0)
        .sort((a, b) => b.row_count - a.row_count)
        .map((c) => ({ table: c.table, row_count: c.row_count })),
    [patientCoverage]
  );

  const rowCountData = useMemo(
    () => [...tables].sort((a, b) => b.row_count - a.row_count).map((t) => ({ table: t.table, row_count: t.row_count })),
    [tables]
  );

  const patientCountData = useMemo(
    () =>
      tables
        .filter((t) => t.patient_count > 0)
        .sort((a, b) => b.patient_count - a.patient_count)
        .map((t) => ({ table: t.table, patient_count: t.patient_count })),
    [tables]
  );

  const heatmapTables = useMemo(() => tables.filter((t) => Object.keys(t.null_rates || {}).length > 0), [tables]);

  return (
    <div className="slide-up">
      <PageHeader
        eyebrow="TRACK 2 · MEASUREMENT COVERAGE"
        title="Coverage Explorer"
        description="An explainable view of measurement coverage, unit variation, coding patterns, and data provenance across the demo cohort — so researchers can judge whether the data actually fit their analysis."
      />

      {status === 'loading' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <SkeletonChartCard height={240} />
          <SkeletonChartCard height={240} />
          <SkeletonChartCard height={160} />
        </div>
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

      {status === 'ready' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35 }}
          style={{ display: 'flex', flexDirection: 'column', gap: 18 }}
        >
          {/* (1) Row counts per table */}
          <SpotlightCard style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <Table size={20} color="var(--accent)" />
              <strong>Row count by table</strong>
              <span className="chip chip--ok" style={{ marginLeft: 'auto' }}>
                {tables.length} tables
              </span>
            </div>
            <StatBarChart data={rowCountData} dataKey="row_count" unitLabel="rows" gradientId="rowCountFill" />
          </SpotlightCard>

          {/* (3) Patient count per table */}
          <SpotlightCard style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <Users size={20} color="var(--accent)" />
              <strong>Distinct patients per table</strong>
              <span className="chip chip--ok" style={{ marginLeft: 'auto' }}>
                of 100 in demo
              </span>
            </div>
            <StatBarChart data={patientCountData} dataKey="patient_count" unitLabel="patients" gradientId="patientCountFill" />
          </SpotlightCard>

          {/* (2) Null-rate heatmap */}
          <SpotlightCard style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
              <ChartDonut size={20} color="var(--accent)" />
              <strong>Null rate by column</strong>
            </div>
            <NullRateHeatmap tables={heatmapTables} />
          </SpotlightCard>

          {/* B3.7 — Patient-level drill-down */}
          <SpotlightCard style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18, flexWrap: 'wrap' }}>
              <UserCircle size={20} color="var(--accent)" />
              <strong>Patient data coverage</strong>
              {allPatients.length > 0 && (
                <select
                  value={selectedPatient ?? ''}
                  onChange={(e) => handlePatientChange(Number(e.target.value))}
                  className="mono"
                  style={{
                    marginLeft: 'auto',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--card-border)',
                    background: '#fff',
                    color: 'var(--text-primary)',
                    fontSize: '0.8rem',
                  }}
                >
                  {allPatients.map((p) => (
                    <option key={p.subject_id} value={p.subject_id}>
                      Patient {p.subject_id} · {p.gender}, {p.anchor_age}y
                    </option>
                  ))}
                </select>
              )}
            </div>

            {patientStatus === 'loading' && <LoadingState label="Loading patient coverage…" />}

            {patientStatus === 'ready' && patientCoverage && (
              <>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 20 }}>
                  <div className="card" style={{ padding: '12px 18px', flex: 1, minWidth: 140 }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)', marginBottom: 4 }}>ADMISSIONS</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{patientCoverage.admission_count}</div>
                  </div>
                  <div className="card" style={{ padding: '12px 18px', flex: 1, minWidth: 140 }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)', marginBottom: 4 }}>TABLES WITH DATA</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>
                      {patientCoverage.coverage.filter((c) => c.has_data).length}
                      <span style={{ fontSize: '0.9rem', color: 'var(--text-tertiary)' }}> / {patientCoverage.coverage.length}</span>
                    </div>
                  </div>
                </div>

                {/* Table presence chips */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 20 }}>
                  {patientCoverage.coverage.map((c) => (
                    <span
                      key={c.table}
                      className="mono"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        fontSize: '0.7rem',
                        padding: '4px 10px',
                        borderRadius: 999,
                        border: '1px solid var(--card-border)',
                        color: c.has_data ? 'var(--accent)' : 'var(--text-tertiary)',
                        background: c.has_data ? 'var(--accent-dim)' : 'transparent',
                      }}
                    >
                      {c.has_data ? <CheckCircle size={11} weight="fill" /> : <XCircle size={11} />}
                      {c.table}
                    </span>
                  ))}
                </div>

                {/* Measurement frequency per table */}
                {patientFreqData.length > 0 && (
                  <>
                    <strong style={{ fontSize: '0.85rem', display: 'block', marginBottom: 10 }}>
                      Row count per table for this patient
                    </strong>
                    <StatBarChart data={patientFreqData} dataKey="row_count" unitLabel="rows" gradientId="patientFreqFill" height={200} />
                  </>
                )}
              </>
            )}

            {patientStatus === 'error' && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Could not load coverage for this patient.</p>
            )}
          </SpotlightCard>
        </motion.div>
      )}
    </div>
  );
}
