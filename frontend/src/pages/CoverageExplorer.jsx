import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ChartDonut, Table, Users } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import SpotlightCard from '../components/SpotlightCard';
import StatBarChart from '../components/StatBarChart';
import NullRateHeatmap from '../components/NullRateHeatmap';
import { API_BASE_URL, apiGet } from '../lib/api';

export default function CoverageExplorer() {
  const [status, setStatus] = useState('loading');
  const [tables, setTables] = useState([]);

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

      {status === 'loading' && <LoadingState label={`Connecting to ${API_BASE_URL}`} />}

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
        </motion.div>
      )}
    </div>
  );
}
