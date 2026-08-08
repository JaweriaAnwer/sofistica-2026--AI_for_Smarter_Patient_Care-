import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { MagnifyingGlassPlus } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import SpotlightCard from '../components/SpotlightCard';
import AnimatedCounter from '../components/AnimatedCounter';
import { API_BASE_URL, apiGet } from '../lib/api';

export default function CohortBuilder() {
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    apiGet('/api/health')
      .then(() => !cancelled && setStatus('ready'))
      .catch(() => !cancelled && setStatus('error'));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="slide-up">
      <PageHeader
        eyebrow="TRACK 2 · COHORT DEFINITION"
        title="Cohort Builder"
        description="Turn a plain-language research question into a structured, patient-grouped cohort query with visible inclusion and exclusion logic — every filter traces back to a source table and field."
      />

      {status === 'loading' && <LoadingState label={`Connecting to ${API_BASE_URL}`} />}

      {status === 'error' && (
        <div className="card" style={{ padding: 20, borderColor: 'rgba(255,107,107,0.35)' }}>
          <span className="chip chip--error">Backend unreachable</span>
          <p style={{ color: 'var(--text-secondary)', marginTop: 10, marginBottom: 0 }}>
            No response from <code className="mono">{API_BASE_URL}</code>. This page will populate once
            Member C's cohort endpoint is live — the UI shell works standalone in the meantime.
          </p>
        </div>
      )}

      {(status === 'ready' || status === 'idle') && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
        >
          <SpotlightCard style={{ padding: 24, marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <MagnifyingGlassPlus size={20} color="var(--accent)" />
              <strong>Define a cohort</strong>
              <span className="chip chip--ok" style={{ marginLeft: 'auto' }}>
                placeholder
              </span>
            </div>
            <p style={{ color: 'var(--text-tertiary)', fontSize: '0.9rem' }}>
              Natural-language query input, inclusion/exclusion rule list, and matching patient count
              go here once the cohort API is wired up.
            </p>
          </SpotlightCard>

          <div style={{ display: 'flex', gap: 16 }}>
            <SpotlightCard style={{ padding: '18px 22px', flex: 1 }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: 6 }}>
                PATIENTS IN DEMO
              </div>
              <AnimatedCounter value={100} style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent)' }} />
            </SpotlightCard>
            <SpotlightCard style={{ padding: '18px 22px', flex: 1 }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: 6 }}>
                MATCHING COHORT
              </div>
              <AnimatedCounter value={0} style={{ fontSize: '1.6rem', fontWeight: 700 }} />
            </SpotlightCard>
          </div>
        </motion.div>
      )}
    </div>
  );
}
