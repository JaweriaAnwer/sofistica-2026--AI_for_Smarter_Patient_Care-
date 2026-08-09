import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { PencilSimple, Play, Copy, Check } from '@phosphor-icons/react';

/**
 * SQLEditor — displays generated/edited SQL with syntax highlighting.
 * "Edit" swaps to a plain monospace textarea; "Run" re-executes whatever
 * SQL is currently in the box via onRun (POST /api/cohort/execute),
 * which lets a researcher tweak the AI's query and see updated results
 * without going back through the LLM.
 */
export default function SQLEditor({ sql, onRun, running }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(sql);
  const [copied, setCopied] = useState(false);

  // Keep the draft in sync if a new SQL string arrives from outside (e.g.
  // a fresh LLM response or template selection) while not mid-edit.
  if (!editing && draft !== sql) setDraft(sql);

  function handleCopy() {
    navigator.clipboard.writeText(editing ? draft : sql).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '10px 14px',
          borderBottom: '1px solid var(--card-border)',
          background: 'rgba(15,23,42,0.02)',
        }}
      >
        <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontWeight: 600 }}>
          GENERATED SQL
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button type="button" className="btn btn--ghost" style={{ padding: '5px 10px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: 5 }} onClick={handleCopy}>
            {copied ? <Check size={13} color="var(--accent)" /> : <Copy size={13} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            style={{ padding: '5px 10px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: 5 }}
            onClick={() => setEditing((e) => !e)}
          >
            <PencilSimple size={13} />
            {editing ? 'Preview' : 'Edit'}
          </button>
          <button
            type="button"
            className="btn btn--primary"
            style={{ padding: '5px 12px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: 5 }}
            onClick={() => onRun(editing ? draft : sql)}
            disabled={running}
          >
            <Play size={13} weight="fill" />
            {running ? 'Running…' : 'Run'}
          </button>
        </div>
      </div>

      {editing ? (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          spellCheck={false}
          className="mono"
          style={{
            width: '100%',
            minHeight: 180,
            padding: 16,
            border: 'none',
            outline: 'none',
            resize: 'vertical',
            fontSize: '0.82rem',
            lineHeight: 1.6,
            background: '#282a36', // matches dracula bg so the swap is seamless
            color: '#f8f8f2',
          }}
        />
      ) : (
        <SyntaxHighlighter language="sql" style={dracula} customStyle={{ margin: 0, padding: 16, fontSize: '0.82rem', borderRadius: 0 }}>
          {sql || '-- No query yet'}
        </SyntaxHighlighter>
      )}
    </div>
  );
}
