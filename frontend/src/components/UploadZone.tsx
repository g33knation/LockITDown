import React, { useCallback } from 'react';

interface UploadZoneProps {
    onFilesSelect: (files: File[]) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onFilesSelect }) => {

    const scanFiles = async (entry: FileSystemEntry, files: File[]) => {
        if (entry.isFile) {
            const fileEntry = entry as FileSystemFileEntry;
            return new Promise<void>((resolve) => {
                fileEntry.file((file) => {
                    files.push(file);
                    resolve();
                });
            });
        } else if (entry.isDirectory) {
            const dirEntry = entry as FileSystemDirectoryEntry;
            const reader = dirEntry.createReader();
            return new Promise<void>((resolve) => {
                reader.readEntries(async (entries) => {
                    const promises = entries.map((e) => scanFiles(e, files));
                    await Promise.all(promises);
                    resolve();
                });
            });
        }
    };

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        const items = e.dataTransfer.items;
        const files: File[] = [];

        if (items) {
            const promises = [];
            for (let i = 0; i < items.length; i++) {
                const item = items[i].webkitGetAsEntry();
                if (item) {
                    promises.push(scanFiles(item, files));
                }
            }
            await Promise.all(promises);
            if (files.length > 0) {
                onFilesSelect(files);
            }
        } else if (e.dataTransfer.files) {
            // Fallback
            onFilesSelect(Array.from(e.dataTransfer.files));
        }
    }, [onFilesSelect]);

    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            onFilesSelect(Array.from(e.target.files));
        }
    }, [onFilesSelect]);

    return (
        <div
            className="border-2 border-dashed border-slate-600 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer bg-slate-800/50"
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
        >
            <input
                type="file"
                className="hidden"
                id="file-upload"
                onChange={handleChange}
                multiple
                {...{ webkitdirectory: "" } as any}
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
                <div className="text-4xl mb-4">📂</div>
                <h3 className="text-xl font-semibold mb-2 text-slate-200">Drag & Drop Folder or Files</h3>
                <p className="text-slate-400">Recursive scan supported</p>
            </label>
        </div>
    );
};
