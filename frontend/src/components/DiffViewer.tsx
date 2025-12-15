import React from 'react';

interface DiffViewerProps {
    original: string;
    fixed: string;
    explanation: string;
    onApply: () => void;
    onCancel: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ original, fixed, explanation, onApply, onCancel }) => {
    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
            <div className="bg-slate-900 rounded-xl w-full max-w-6xl h-[90vh] flex flex-col border border-slate-700 shadow-2xl">

                {/* Header */}
                <div className="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-800">
                    <div>
                        <h2 className="text-2xl font-bold text-white mb-1">Review Fix</h2>
                        <p className="text-slate-400 text-sm">{explanation}</p>
                    </div>
                    <div className="flex gap-4">
                        <button
                            onClick={onCancel}
                            className="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-700 transition"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={onApply}
                            className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition shadow-lg shadow-blue-900/20"
                        >
                            Apply Fix
                        </button>
                    </div>
                </div>

                {/* Diff Content */}
                <div className="flex-1 overflow-hidden flex divide-x divide-slate-700">
                    {/* Original */}
                    <div className="flex-1 flex flex-col bg-red-950/10">
                        <div className="p-3 bg-red-900/20 text-red-200 text-xs font-mono uppercase tracking-wider border-b border-red-900/20">
                            Original Vulnerable Code
                        </div>
                        <pre className="flex-1 p-4 overflow-auto font-mono text-sm text-red-100/80 whitespace-pre-wrap">
                            <code>{original}</code>
                        </pre>
                    </div>

                    {/* Fixed */}
                    <div className="flex-1 flex flex-col bg-green-950/10">
                        <div className="p-3 bg-green-900/20 text-green-200 text-xs font-mono uppercase tracking-wider border-b border-green-900/20">
                            Proposed Secure Fix
                        </div>
                        <pre className="flex-1 p-4 overflow-auto font-mono text-sm text-green-100/80 whitespace-pre-wrap">
                            <code>{fixed}</code>
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
};
