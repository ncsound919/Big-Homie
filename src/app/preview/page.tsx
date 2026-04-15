'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

const PREVIEW_PROJECT_STORAGE_KEY = 'agentbrowser:preview';
const GENERATED_HTML_STORAGE_KEY = 'agentbrowser:generated-html';
const GENERATED_META_STORAGE_KEY = 'agentbrowser:generated-meta';

interface PreviewSnapshot {
  name: string;
  description: string;
  type?: string;
  audience?: string;
}

function getPreviewFingerprint(project: PreviewSnapshot): string {
  return JSON.stringify(project);
}

/**
 * Preview Page — renders the real generated HTML from the build pipeline.
 *
 * Flow:
 * 1. On mount, reads `agentbrowser:generated-html` from localStorage (set by page.tsx after generation)
 * 2. If not found, calls /api/generate with project data from `agentbrowser:preview`
 * 3. Renders the HTML inside a sandboxed iframe
 */
export default function PreviewPage() {
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const didFetch = useRef(false);

  const loadPreview = useCallback(async () => {
    const projectRaw = localStorage.getItem(PREVIEW_PROJECT_STORAGE_KEY);
    if (!projectRaw) {
      setError('No project data found. Go back and build something first.');
      setLoading(false);
      return;
    }

    try {
      const project = JSON.parse(projectRaw) as PreviewSnapshot;
      const expectedFingerprint = getPreviewFingerprint(project);
      const generatedHtml = localStorage.getItem(GENERATED_HTML_STORAGE_KEY);
      const generatedMeta = localStorage.getItem(GENERATED_META_STORAGE_KEY);

      if (generatedHtml && generatedMeta === expectedFingerprint) {
        setHtml(generatedHtml);
        setLoading(false);
        return;
      }

      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(project),
      });
      if (!res.ok) throw new Error('Generation failed');
      const data = (await res.json()) as { html: string };
      setHtml(data.html);
      try {
        localStorage.setItem(GENERATED_HTML_STORAGE_KEY, data.html);
        localStorage.setItem(GENERATED_META_STORAGE_KEY, expectedFingerprint);
      } catch {
        // ignore quota
      }
    } catch (err) {
      setError(`Failed to generate preview: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (didFetch.current) return;
    didFetch.current = true;
    loadPreview();
  }, [loadPreview]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0a12', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 20, fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ width: 48, height: 48, border: '3px solid #7c3aed', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
        <p style={{ color: '#8890a4', fontSize: 14 }}>Generating your site...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0a12', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16, fontFamily: 'system-ui, sans-serif' }}>
        <p style={{ color: '#f87171', fontSize: 16, fontWeight: 600 }}>Something went wrong</p>
        <p style={{ color: '#8890a4', fontSize: 14, maxWidth: 400, textAlign: 'center' }}>{error}</p>
        <a href="/" style={{ color: '#7c3aed', textDecoration: 'none', fontSize: 14, marginTop: 8 }}>← Back to AgentBrowser</a>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#0a0a12' }}>
      {/* Toolbar */}
      <div style={{ height: 40, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px', background: '#15152a', borderBottom: '1px solid #252830', flexShrink: 0, fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <a href="/" style={{ color: '#8890a4', fontSize: 12, textDecoration: 'none' }}>← Back to AgentBrowser</a>
          <span style={{ color: '#3b3b50' }}>|</span>
          <span style={{ color: '#8890a4', fontSize: 12 }}>Live Preview</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => {
              if (html) {
                const blob = new Blob([html], { type: 'text/html' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'index.html';
                a.click();
                URL.revokeObjectURL(url);
              }
            }}
            style={{ padding: '4px 12px', borderRadius: 6, background: '#7c3aed', color: '#fff', border: 'none', fontSize: 11, fontWeight: 600, cursor: 'pointer' }}
          >
            Download HTML
          </button>
          <button
            onClick={() => {
              if (html) {
                const blob = new Blob([html], { type: 'text/html' });
                const url = URL.createObjectURL(blob);
                window.open(url, '_blank', 'noopener,noreferrer');
                window.setTimeout(() => URL.revokeObjectURL(url), 1000);
              }
            }}
            style={{ padding: '4px 12px', borderRadius: 6, background: 'transparent', color: '#8890a4', border: '1px solid #252830', fontSize: 11, fontWeight: 600, cursor: 'pointer' }}
          >
            Open Full Page
          </button>
        </div>
      </div>

      {/* Iframe */}
      <iframe
        title="Site Preview"
        sandbox="allow-forms"
        srcDoc={html ?? ''}
        style={{ flex: 1, border: 'none', background: '#fff', width: '100%' }}
      />
    </div>
  );
}
