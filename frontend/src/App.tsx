import { useState } from 'react';
import { PathInput } from './components/PathInput';
import { DiffViewer } from './components/DiffViewer';

interface Vulnerability {
  id: string;
  line: number;
  content: string;
  type: string;
  severity: string;
}

interface AnalyzedFile {
  filename: string;
  filepath: string;
  content: string;
  vulnerabilities: Vulnerability[];
}

interface FixProposal {
  original_snippet: string;
  fixed_snippet: string;
  explanation: string;
}

function App() {
  const [analyzedFiles, setAnalyzedFiles] = useState<AnalyzedFile[]>([]);
  const [selectedFileIndex, setSelectedFileIndex] = useState<number | null>(null);
  const [currentScanPath, setCurrentScanPath] = useState<string>("");
  const [showErrorsOnly, setShowErrorsOnly] = useState(false);

  const [selectedVuln, setSelectedVuln] = useState<Vulnerability | null>(null);
  const [fixProposal, setFixProposal] = useState<FixProposal | null>(null);
  const [loading, setLoading] = useState(false);

  const API_URL = 'http://localhost:8000/api';

  const handleScanPath = async (path: string) => {
    setCurrentScanPath(path);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/scan-path`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });

      if (!res.ok) {
        throw new Error(`Scan failed with status: ${res.status}`);
      }

      const data = await res.json();

      if (data.files && Array.isArray(data.files)) {
        setAnalyzedFiles(data.files);
        if (data.files.length > 0) {
          setSelectedFileIndex(0);
        } else {
          alert("No supported files found in directory.");
        }
      } else {
        console.error("Unexpected response:", data);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to scan path. Ensure the path exists and the backend has access.');
    } finally {
      setLoading(false);
    }
  };

  const handleVulnClick = async (vuln: Vulnerability) => {
    if (selectedFileIndex === null) return;

    setSelectedVuln(vuln);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/generate-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vulnerability_id: vuln.id,
          line: vuln.line,
          content: vuln.content
        }),
      });
      const data = await res.json();
      setFixProposal(data);
    } catch (err) {
      console.error(err);
      alert('Failed to generate fix');
    } finally {
      setLoading(false);
    }
  };

  const applyFix = async () => {
    if (!selectedVuln || !fixProposal || selectedFileIndex === null) return;
    const currentFile = analyzedFiles[selectedFileIndex];

    try {
      const res = await fetch(`${API_URL}/apply-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: currentFile.filepath,
          line: selectedVuln.line,
          new_content: fixProposal.fixed_snippet
        }),
      });

      if (res.ok) {
        alert('Fix applied! Refreshing results...');
        setFixProposal(null);
        setSelectedVuln(null);
        // Refresh the scan
        await handleScanPath(currentScanPath);
      } else {
        alert('Failed to apply fix');
      }
    } catch (err) {
      console.error(err);
      alert('Error applying fix');
    }
  };

  const handleVerify = async (e: React.MouseEvent, vuln: Vulnerability) => {
    e.stopPropagation(); // Prevent opening Fix Modal
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/verify-vuln`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: vuln.content,
          type: vuln.type
        }),
      });
      const data = await res.json();
      
      const emoji = data.is_false_positive ? "🟢" : "🔴";
      const title = data.is_false_positive ? "Likely False Positive" : "True Positive";
      
      alert(`${emoji} ${title} (Confidence: ${(data.confidence * 100).toFixed(1)}%)\n\nReasoning:\n${data.reasoning}`);
      
    } catch (err) {
      console.error(err);
      alert('Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  const currentFile = selectedFileIndex !== null ? analyzedFiles[selectedFileIndex] : null;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      <header className="flex-none p-4 border-b border-slate-700 bg-slate-800 flex items-center gap-4 z-10">
        <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">🛡️</div>
        <h1 className="font-bold text-lg">Code Security Auditor</h1>
        {analyzedFiles.length > 0 && (
          <button
            onClick={() => { setAnalyzedFiles([]); setSelectedFileIndex(null); }}
            className="ml-auto text-sm text-slate-400 hover:text-white"
          >
            New Scan
          </button>
        )}
      </header>

      <div className="flex-1 flex overflow-hidden">
        {analyzedFiles.length === 0 ? (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-xl">
              <PathInput onScanConfigured={handleScanPath} />
            </div>
          </div>
        ) : (
          <>
            {/* Sidebar */}
            <div className="w-64 flex-none bg-slate-900 border-r border-slate-700 overflow-y-auto">
              <div className="p-4 bg-slate-800 border-b border-slate-700">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Files ({analyzedFiles.length})
                </div>
                <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showErrorsOnly}
                    onChange={(e) => setShowErrorsOnly(e.target.checked)}
                    className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-offset-slate-800"
                  />
                  <span>Show Errors Only</span>
                </label>
              </div>
              <ul className="space-y-0.5">
                {analyzedFiles.map((file, idx) => {
                  const vulnCount = file.vulnerabilities.length;
                  const hasVulns = vulnCount > 0;

                  if (showErrorsOnly && !hasVulns) return null;

                  return (
                    <li key={idx}>
                      <button
                        onClick={() => setSelectedFileIndex(idx)}
                        className={`w-full text-left px-4 py-3 text-sm flex items-center justify-between group transition-colors ${selectedFileIndex === idx
                          ? 'bg-blue-900/20 text-blue-200 border-r-2 border-blue-500'
                          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                          }`}
                      >
                        <span className="truncate" title={file.filename}>{file.filename}</span>
                        {hasVulns && (
                          <span className="flex-none px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-400 text-xs font-bold">
                            {vulnCount}
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* Main Area */}
            <div className="flex-1 overflow-y-auto p-8">
              {currentFile ? (
                <div className="max-w-4xl mx-auto space-y-6">
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold">{currentFile.filename}</h2>
                    <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-xs font-mono">
                      {currentFile.filepath}
                    </span>
                  </div>

                  {currentFile.vulnerabilities.length === 0 ? (
                    <div className="p-8 bg-green-500/5 rounded-xl border border-green-500/20 text-green-300 flex items-center gap-3">
                      <span>✅</span> No issues detected in this file.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {currentFile.vulnerabilities.map((vuln) => (
                        <div
                          key={vuln.id}
                          className="bg-slate-800 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition cursor-pointer group"
                          onClick={() => handleVulnClick(vuln)}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-red-400 font-bold text-sm">Line {vuln.line}</span>
                              <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-300 text-xs border border-red-500/20 uppercase tracking-wide">
                                {vuln.severity}
                              </span>
                            </div>
                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition">
                                <button 
                                    onClick={(e) => handleVerify(e, vuln)}
                                    className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-1 rounded border border-slate-600"
                                    title="Ask AI if this is a False Positive"
                                >
                                    🤔 Verify
                                </button>
                                <button className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded">
                                    Fix It
                                </button>
                            </div>
                          </div>
                          <div className="font-mono text-sm bg-slate-950 p-3 rounded text-slate-300 overflow-x-auto">
                            {vuln.content.trim()}
                          </div>
                          <div className="mt-2 text-sm text-slate-400">
                            {vuln.type} detects a potential security risk.
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-slate-500 mt-20">Select a file from the sidebar</div>
              )}
            </div>
          </>
        )}
      </div>

      {loading && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="animate-spin text-4xl">⏳</div>
        </div>
      )}

      {fixProposal && selectedVuln && (
        <DiffViewer
          original={fixProposal.original_snippet}
          fixed={fixProposal.fixed_snippet}
          explanation={fixProposal.explanation}
          onApply={applyFix}
          onCancel={() => { setFixProposal(null); setSelectedVuln(null); }}
        />
      )}
    </div>
  );
}

export default App;
