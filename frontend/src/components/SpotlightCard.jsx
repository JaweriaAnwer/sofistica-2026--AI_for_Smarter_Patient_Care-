import { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

/**
 * SpotlightCard
 * Interaction pattern adapted from KokonutUI's "Spotlight Cards" component
 * (https://kokonutui.com — kokonut-labs/kokonutui, MIT license, © 2025 kokonutUI):
 * a subtle 3D tilt toward the cursor, a radial glow that follows it, and a
 * diagonal shimmer sweep on hover. Reimplemented here in plain React/CSS
 * (no Tailwind) against ClinIQ's own design tokens instead of copying the
 * source file directly.
 */
const TILT_MAX = 6;
const TILT_SPRING = { stiffness: 300, damping: 28 };
const GLOW_SPRING = { stiffness: 180, damping: 22 };

export default function SpotlightCard({ children, style, className = '', accent = 'var(--accent)', ...props }) {
  const ref = useRef(null);
  const [shimmer, setShimmer] = useState(false);

  const normX = useMotionValue(0.5);
  const normY = useMotionValue(0.5);
  const glowOpacity = useSpring(0, GLOW_SPRING);

  const rotateX = useSpring(useTransform(normY, [0, 1], [TILT_MAX, -TILT_MAX]), TILT_SPRING);
  const rotateY = useSpring(useTransform(normX, [0, 1], [-TILT_MAX, TILT_MAX]), TILT_SPRING);

  const glowX = useTransform(normX, (v) => `${v * 100}%`);
  const glowY = useTransform(normY, (v) => `${v * 100}%`);
  const glowBackground = useTransform([glowX, glowY], ([x, y]) =>
    `radial-gradient(280px circle at ${x} ${y}, ${accent}33, transparent 70%)`
  );

  function handleMouseMove(e) {
    const rect = ref.current.getBoundingClientRect();
    normX.set((e.clientX - rect.left) / rect.width);
    normY.set((e.clientY - rect.top) / rect.height);
  }

  function handleMouseEnter() {
    glowOpacity.set(1);
    setShimmer(true);
  }

  function handleMouseLeave() {
    normX.set(0.5);
    normY.set(0.5);
    glowOpacity.set(0);
  }

  return (
    <motion.div
      ref={ref}
      className={`card ${className}`}
      style={{
        position: 'relative',
        overflow: 'hidden',
        rotateX,
        rotateY,
        transformPerspective: 900,
        ...style,
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      {...props}
    >
      {/* Static accent tint */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: `radial-gradient(ellipse at 20% 20%, ${accent}14, transparent 65%)`,
        }}
      />
      {/* Cursor-tracking glow */}
      <motion.div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: glowOpacity,
          background: glowBackground,
        }}
      />
      {/* Shimmer sweep */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: '0 auto 0 0',
          width: '55%',
          pointerEvents: 'none',
          transform: shimmer ? 'translateX(280%) skewX(-12deg)' : 'translateX(-100%) skewX(-12deg)',
          transition: 'transform 0.7s ease-out',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.045), transparent)',
        }}
      />
      <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
    </motion.div>
  );
}
