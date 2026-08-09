import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

function CustomTooltip({ active, payload, label, unitLabel }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card" style={{ padding: '8px 12px', border: '1px solid var(--card-border-hover)' }}>
      <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{label}</div>
      <div className="mono" style={{ fontSize: '0.9rem', color: 'var(--accent)', fontWeight: 600 }}>
        {payload[0].value.toLocaleString()} {unitLabel}
      </div>
    </div>
  );
}

/**
 * StatBarChart — reusable animated Recharts bar chart against a single
 * numeric field. Used twice on the Coverage Explorer: once for per-table
 * row counts, once for per-table patient counts.
 */
export default function StatBarChart({ data, dataKey, xKey = 'table', unitLabel = '', gradientId, height = 240 }) {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2563eb" stopOpacity={0.95} />
              <stop offset="100%" stopColor="#2563eb" stopOpacity={0.25} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(15,23,42,0.08)" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={{ stroke: 'rgba(15,23,42,0.12)' }}
            tickLine={false}
            interval={0}
            angle={-35}
            textAnchor="end"
            height={60}
          />
          <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={44} />
          <Tooltip content={<CustomTooltip unitLabel={unitLabel} />} cursor={{ fill: 'rgba(37,99,235,0.06)' }} />
          <Bar dataKey={dataKey} fill={`url(#${gradientId})`} radius={[6, 6, 0, 0]} animationDuration={900} animationEasing="ease-out" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
