/**
 * Skeleton — pulsing placeholder blocks shown while an API call is in
 * flight, shaped to roughly match the content that will replace them
 * (scorecards, chart panels, table rows) so the layout doesn't jump when
 * real data arrives. Prefer this over a spinner for anything that takes
 * more than a beat, since it shows the *shape* of what's coming.
 */
function Block({ width = '100%', height = 16, radius = 6, style }) {
  return (
    <div
      className="skeleton-pulse"
      style={{
        width,
        height,
        borderRadius: radius,
        background: 'rgba(15, 23, 42, 0.07)',
        ...style,
      }}
    />
  );
}

export function SkeletonScoreCards({ count = 4 }) {
  return (
    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 24 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card" style={{ padding: '18px 20px', flex: 1, minWidth: 140 }}>
          <Block width="60%" height={10} style={{ marginBottom: 12 }} />
          <Block width="40%" height={26} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChartCard({ height = 240 }) {
  return (
    <div className="card" style={{ padding: 24 }}>
      <Block width="30%" height={14} style={{ marginBottom: 18 }} />
      <Block width="100%" height={height} radius={10} />
    </div>
  );
}

export function SkeletonRows({ rows = 4 }) {
  return (
    <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <Block key={i} width={`${86 - i * 6}%`} height={14} />
      ))}
    </div>
  );
}

export default { SkeletonScoreCards, SkeletonChartCard, SkeletonRows };
