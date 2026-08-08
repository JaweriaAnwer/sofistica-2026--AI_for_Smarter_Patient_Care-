import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const PLACEHOLDER_DATA = [
  { table: 'admissions', coverage: 100 },
  { table: 'labevents', coverage: 92 },
  { table: 'chartevents', coverage: 88 },
  { table: 'diagnoses_icd', coverage: 97 },
  { table: 'prescriptions', coverage: 79 },
  { table: 'transfers', coverage: 95 },
];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="card"
      style={{ padding: '8px 12px', border: '1px solid var(--card-border-hover)' }}
    >
      <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{label}</div>
      <div className="mono" style={{ fontSize: '0.9rem', color: 'var(--accent)', fontWeight: 600 }}>
        {payload[0].value}% populated
      </div>
    </div>
  );
}

/**
 * CoverageChart — per-table field-completeness bars. Bars animate in on
 * mount (Recharts' built-in animation) and gradient-fill toward the
 * accent color, so it reads as "alive" rather than a static report chart.
 * Data below is illustrative placeholder — wire to the real coverage
 * endpoint before judging.
 */
export default function CoverageChart({ data = PLACEHOLDER_DATA }) {
  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="coverageFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2563eb" stopOpacity={0.95} />
              <stop offset="100%" stopColor="#2563eb" stopOpacity={0.25} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(15,23,42,0.08)" vertical={false} />
          <XAxis
            dataKey="table"
            tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={{ stroke: 'rgba(15,23,42,0.12)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={36}
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(37,99,235,0.06)' }} />
          <Bar
            dataKey="coverage"
            fill="url(#coverageFill)"
            radius={[6, 6, 0, 0]}
            animationDuration={900}
            animationEasing="ease-out"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
