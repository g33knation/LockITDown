import React, { useState } from 'react';

interface PathInputProps {
    onScanConfigured: (path: string) => void;
}

export const PathInput: React.FC<PathInputProps> = ({ onScanConfigured }) => {
    const [path, setPath] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (path.trim()) {
            onScanConfigured(path.trim());
        }
    };

    const handleBrowse = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/browse');
            const data = await res.json();
            if (data.path) {
                setPath(data.path);
            }
        } catch (err) {
            console.error("Browse failed:", err);
            alert("Failed to open folder picker on server.");
        }
    };

    return (
        <div className="bg-slate-800/50 p-12 rounded-lg border border-slate-700 text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold mb-4 text-slate-200">Scan Local Directory</h3>
            <form onSubmit={handleSubmit} className="flex gap-2 max-w-md mx-auto">
                <input
                    type="text"
                    value={path}
                    onChange={(e) => setPath(e.target.value)}
                    onClick={handleBrowse}
                    placeholder="Click to select folder..."
                    className="flex-1 px-4 py-2 bg-slate-900 border border-slate-600 rounded text-slate-200 focus:outline-none focus:border-blue-500 cursor-pointer hover:bg-slate-800 transition"
                    readOnly
                />
                <button
                    type="button"
                    onClick={handleBrowse}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium rounded transition"
                    title="Browse Folder"
                >
                    📂
                </button>
                <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded transition"
                >
                    Scan
                </button>
            </form>
        </div>
    );
};
