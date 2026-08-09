import { motion } from 'framer-motion';

export default function PageHeader({ eyebrow, title, description }) {
  return (
    <motion.header
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      style={{ marginBottom: 28 }}
    >
      <div
        className="mono"
        style={{ fontSize: '0.72rem', color: 'var(--accent)', letterSpacing: '0.06em', marginBottom: 8 }}
      >
        {eyebrow}
      </div>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }} className="gradient-text">
        {title}
      </h1>
      <p style={{ color: 'var(--text-secondary)', maxWidth: 640, marginTop: 8, lineHeight: 1.55 }}>
        {description}
      </p>
    </motion.header>
  );
}
