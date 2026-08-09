import { useEffect, useRef } from 'react';
import { animate, svg, utils } from 'animejs';

// A stylised ECG waveform: flat baseline, then the classic P-QRS-T complex,
// repeated twice so the loop point is invisible.
const ECG_PATH =
  'M0,40 L60,40 L75,20 L90,60 L105,10 L120,70 L135,40 L200,40 ' +
  'L260,40 L275,20 L290,60 L305,10 L320,70 L335,40 L400,40';

/**
 * HeartbeatLine — an animated ECG trace built with anime.js (not
 * framer-motion): svg.createDrawable animates the stroke drawing itself
 * on a loop, and svg.createMotionPath drives a glowing dot that travels
 * along the same path in sync, like a pulse. Chosen deliberately for the
 * Home hero — a literal "vital sign" for a patient-data tool, and the
 * kind of SVG path-drawing effect anime.js is specifically built for.
 */
export default function HeartbeatLine({ width = 400, height = 80, color = 'var(--accent)' }) {
  const svgRef = useRef(null);
  const dotRef = useRef(null);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || !svgRef.current) return;

    let drawAnimation;
    let dotAnimation;
    let drawable;

    try {
      const pathEl = svgRef.current.querySelector('.ecg-path');
      [drawable] = svg.createDrawable(pathEl);

      drawAnimation = animate(drawable, {
        draw: ['0 0', '0 1', '1 1'],
        ease: 'inOutQuad',
        duration: 2600,
        loop: true,
      });

      if (dotRef.current) {
        const motionPath = svg.createMotionPath(pathEl);
        dotAnimation = animate(dotRef.current, {
          ...motionPath,
          duration: 2600,
          loop: true,
          ease: 'inOutQuad',
        });
      }
    } catch (err) {
      // SVG path geometry APIs occasionally misbehave on older browsers —
      // fail silently to a static (undrawn) trace rather than break the page.
      console.warn('HeartbeatLine animation skipped:', err);
    }

    return () => {
      drawAnimation?.pause();
      dotAnimation?.pause();
      if (drawable) utils.remove(drawable);
    };
  }, []);

  return (
    <svg ref={svgRef} viewBox="0 0 400 80" width={width} height={height} style={{ overflow: 'visible' }} aria-hidden="true">
      <path d={ECG_PATH} className="ecg-path" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.85" />
      <circle ref={dotRef} r="4" fill={color} style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
    </svg>
  );
}
