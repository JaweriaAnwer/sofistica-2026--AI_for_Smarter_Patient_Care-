import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { House, Database, MagnifyingGlassPlus, ChartDonut, Sparkle } from '@phosphor-icons/react';

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: House, end: true },
  { to: '/cohort', label: 'Cohort Builder', icon: MagnifyingGlassPlus },
  { to: '/quality', label: 'Data Quality', icon: Database },
  { to: '/coverage', label: 'Coverage Explorer', icon: ChartDonut },
];

const styles = {
  sidebar: {
    position: 'fixed',
    top: 'var(--banner-h)',
    bottom: 0,
    left: 0,
    width: 'var(--sidebar-w)',
    borderRight: '1px solid var(--card-border)',
    background: 'var(--bg-raised)',
    display: 'flex',
    flexDirection: 'column',
    padding: '24px 14px',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '0 10px',
    marginBottom: 28,
  },
  brandText: {
    fontWeight: 800,
    fontSize: '1.05rem',
    letterSpacing: '-0.01em',
  },
  brandSub: {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.65rem',
    color: 'var(--text-tertiary)',
    marginTop: 2,
  },
  link: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '10px 12px',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    fontSize: '0.875rem',
    fontWeight: 500,
    marginBottom: 4,
    position: 'relative',
  },
  footer: {
    marginTop: 'auto',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.68rem',
    color: 'var(--text-tertiary)',
    padding: '0 10px',
    lineHeight: 1.5,
  },
};

export default function Sidebar() {
  return (
    <nav style={styles.sidebar} aria-label="Primary">
      <div style={styles.brand}>
        <Sparkle size={20} weight="fill" color="var(--accent)" />
        <div>
          <div style={styles.brandText}>ClinIQ</div>
          <div style={styles.brandSub}>MIMIC-IV DEMO v2.2</div>
        </div>
      </div>

      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          style={({ isActive }) => ({
            ...styles.link,
            color: isActive ? 'var(--text-primary)' : styles.link.color,
            background: isActive ? 'var(--accent-dim)' : 'transparent',
          })}
        >
          {({ isActive }) => (
            <>
              <Icon size={18} weight={isActive ? 'fill' : 'regular'} color={isActive ? 'var(--accent)' : undefined} />
              {label}
              {isActive && (
                <motion.div
                  layoutId="nav-active"
                  transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: 4,
                    bottom: 4,
                    width: 3,
                    borderRadius: 4,
                    background: 'var(--accent)',
                  }}
                />
              )}
            </>
          )}
        </NavLink>
      ))}

      <div style={styles.footer}>
        Track 2 — Cohort &amp; Data Quality Explorer
        <br />
        100 patients · educational sample
      </div>
    </nav>
  );
}
