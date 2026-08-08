import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Database } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import SpotlightCard from '../components/SpotlightCard';
import { API_BASE_URL, apiGet } from '../lib/api';

export default function DataQuality() {
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
        eyebrow="TRACK 2 · DATA QUALITY"
        title="Data Quality Inspector"
        description="Surface missing, duplicated, inconsistent, implausible, or temporally misaligned records. Every flag is a documented rule, not a silent fix — nothing here deletes or overwrites the source data."
      />

      {status === 'loading' && <LoadingState label={`Connecting to ${API_BASE_URL}`} />}

      {status === 'error' && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(255,107,107,0.35)' }}>
          <span className="chip chip--error">Backend unreachable</span>
          <p style={{ color: 'var(--text-secondary)', marginTop: 10, marginBottom: 0 }}>
            No response from <code className="mono">{API_BASE_URL}</code>. This page will populate once
            the data-quality endpoint is live.
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
            <Database size={20} color="var(--accent)" />
            <strong>Quality flags</strong>
            <span className="chip chip--warn" style={{ marginLeft: 'auto' }}>
              placeholder
            </span>
          </div>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '0.9rem' }}>
            A table of detected issues (missing values, duplicate events, unit inconsistencies,
            temporal misalignment) with reversible, rule-backed suggested corrections goes here.
          </p>
        </SpotlightCard>
        </motion.div>
      )}
    </div>
  );
}
