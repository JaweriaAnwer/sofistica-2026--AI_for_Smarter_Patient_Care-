import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ChartDonut } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import SpotlightCard from '../components/SpotlightCard';
import CoverageChart from '../components/CoverageChart';
import { API_BASE_URL, apiGet } from '../lib/api';

export default function Coverage() {
  const [status, setStatus] = useState('idle');

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    apiGet('/health')
      .then(() => !cancelled && setStatus('ready'))
      .catch(() => !cancelled && setStatus('error'));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="slide-up">
      <PageHeader
        eyebrow="TRACK 2 · MEASUREMENT COVERAGE"
        title="Coverage Explorer"
        description="An explainable view of measurement coverage, unit variation, coding patterns, and data provenance across the demo cohort — so researchers can judge whether the data actually fit their analysis."
      />

      {status === 'loading' && <LoadingState label={`Connecting to ${API_BASE_URL}`} />}

      {status === 'error' && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(255,107,107,0.35)' }}>
          <span className="chip chip--error">Backend unreachable</span>
          <p style={{ color: 'var(--text-secondary)', marginTop: 10, marginBottom: 0 }}>
            No response from <code className="mono">{API_BASE_URL}</code>. This page will populate once
            the coverage endpoint is live.
          </p>
        </div>
      )}

      {(status === 'ready' || status === 'idle') && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
        >
        <SpotlightCard style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <ChartDonut size={20} color="var(--accent)" />
            <strong>Coverage by table</strong>
            <span className="chip chip--warn" style={{ marginLeft: 'auto' }}>
              placeholder data
            </span>
          </div>
          <CoverageChart />
          <p style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem', marginTop: 12, marginBottom: 0 }}>
            Illustrative field-completeness by source table. Swap <code className="mono">PLACEHOLDER_DATA</code> in{' '}
            <code className="mono">CoverageChart.jsx</code> for the real coverage endpoint response.
          </p>
        </SpotlightCard>
        </motion.div>
      )}
    </div>
  );
}
