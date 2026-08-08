import { useEffect, useRef } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';

/**
 * AnimatedCounter — counts up to `value` when it scrolls/mounts into view.
 * Used for headline stats (e.g. "100 patients", "12 flags found") so the
 * numbers feel alive rather than static, without pulling in a separate
 * animation library.
 */
export default function AnimatedCounter({ value, duration = 1.1, style }) {
  const ref = useRef(null);
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v).toLocaleString());

  useEffect(() => {
    const controls = animate(count, value, { duration, ease: [0.16, 1, 0.3, 1] });
    return controls.stop;
  }, [value, duration]);

  return (
    <motion.span ref={ref} className="mono" style={style}>
      {rounded}
    </motion.span>
  );
}
