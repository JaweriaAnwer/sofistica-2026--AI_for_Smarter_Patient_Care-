import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Database, MagnifyingGlassPlus, ChartDonut, ArrowRight, Sparkle } from '@phosphor-icons/react';
import SpotlightCard from '../components/SpotlightCard';
import HeartbeatLine from '../components/HeartbeatLine';

const TOOLS = [
  {
    to: '/cohort',
    icon: MagnifyingGlassPlus,
    title: 'Cohort Builder',
    description: 'Turn a research question into a structured, traceable patient cohort.',
  },
  {
    to: '/quality',
    icon: Database,
    title: 'Data Quality Inspector',
    description: 'Surface missing, duplicated, or misaligned records — nothing silently changed.',
  },
  {
    to: '/coverage',
    icon: ChartDonut,
    title: 'Coverage Explorer',
    description: 'See measurement coverage and coding patterns before you trust an analysis.',
  },
];

export default function Home() {
  return (
    <div className="slide-up" style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '48px 12px 8px', position: 'relative' }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            borderRadius: 999,
            background: 'var(--accent-dim)',
            color: 'var(--accent)',
            fontSize: '0.72rem',
            fontWeight: 600,
            marginBottom: 20,
          }}
          className="mono"
        >
          <Sparkle size={14} weight="fill" />
          SOFSTICA AI HACKATHON · TRACK 2
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
          className="gradient-text"
          style={{ fontSize: '3rem', fontWeight: 800, letterSpacing: '-0.03em', margin: 0, lineHeight: 1.05 }}
        >
          ClinIQ
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          style={{ color: 'var(--text-secondary)', maxWidth: 520, margin: '14px auto 0', lineHeight: 1.6 }}
        >
          An AI-powered cohort builder and data quality inspector for the MIMIC-IV Clinical
          Database Demo — built to make structured hospital data easier to trust, one traceable
          row at a time.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          style={{ display: 'flex', justifyContent: 'center', margin: '20px 0 4px' }}
        >
          <HeartbeatLine width={280} height={56} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
          style={{ marginTop: 26, display: 'flex', gap: 12, justifyContent: 'center' }}
        >
          <Link to="/cohort" className="btn btn--primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}>
            Start building a cohort <ArrowRight size={15} weight="bold" />
          </Link>
          <Link to="/quality" className="btn btn--ghost" style={{ textDecoration: 'none' }}>
            Inspect data quality
          </Link>
        </motion.div>

        {/* Ambient animated blobs behind the hero */}
        <motion.div
          aria-hidden="true"
          animate={{ x: [0, 24, 0], y: [0, -14, 0] }}
          transition={{ duration: 9, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            position: 'absolute',
            top: -40,
            left: '18%',
            width: 220,
            height: 220,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(37,99,235,0.14), transparent 70%)',
            zIndex: -1,
            filter: 'blur(4px)',
          }}
        />
        <motion.div
          aria-hidden="true"
          animate={{ x: [0, -20, 0], y: [0, 16, 0] }}
          transition={{ duration: 11, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            position: 'absolute',
            top: -20,
            right: '16%',
            width: 260,
            height: 260,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(37,99,235,0.1), transparent 70%)',
            zIndex: -1,
            filter: 'blur(4px)',
          }}
        />
      </div>

      {/* Tool cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 18 }}>
        {TOOLS.map(({ to, icon: Icon, title, description }, i) => (
          <motion.div
            key={to}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.3 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
          >
            <Link to={to} style={{ textDecoration: 'none', color: 'inherit' }}>
              <SpotlightCard style={{ padding: 22, height: '100%' }}>
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    background: 'var(--accent-dim)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 14,
                  }}
                >
                  <Icon size={19} color="var(--accent)" weight="bold" />
                </div>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.5 }}>
                  {description}
                </div>
              </SpotlightCard>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
