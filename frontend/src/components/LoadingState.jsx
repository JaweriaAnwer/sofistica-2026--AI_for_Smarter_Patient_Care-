import { motion } from 'framer-motion';

/**
 * LoadingState
 * Ring animation adapted from KokonutUI's "Loader" component
 * (https://kokonutui.com — kokonut-labs/kokonutui, MIT license, © 2025 kokonutUI):
 * three counter-rotating conic-gradient rings masked into thin arcs. Ported
 * to plain CSS custom properties (var(--accent)) instead of Tailwind classes.
 */
export default function LoadingState({ label = 'Loading' }) {
  const ring = (deg, duration, opacity, reverse) => ({
    position: 'absolute',
    inset: 0,
    borderRadius: '50%',
    background: `conic-gradient(from ${deg}deg, transparent 0deg, var(--accent) 90deg, transparent 180deg)`,
    mask: 'radial-gradient(circle at 50% 50%, transparent 40%, black 44%, black 48%, transparent 52%)',
    WebkitMask: 'radial-gradient(circle at 50% 50%, transparent 40%, black 44%, black 48%, transparent 52%)',
    opacity,
  });

  return (
    <div
      className="card fade-in"
      style={{
        padding: '40px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
        color: 'var(--text-tertiary)',
      }}
    >
      <div style={{ position: 'relative', width: 44, height: 44 }}>
        <motion.div
          style={ring(0, 3, 0.85)}
          animate={{ rotate: 360 }}
          transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          style={ring(180, 3, 0.4)}
          animate={{ rotate: -360 }}
          transition={{ duration: 3.4, repeat: Infinity, ease: 'linear' }}
        />
      </div>
      <span className="mono" style={{ fontSize: '0.75rem' }}>
        {label}
      </span>
    </div>
  );
}
