import React, { useState } from 'react';
import { Upload, Music, X } from 'lucide-react';

export default function MP3DragDrop() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const file = files[0];
      if (file.type === 'audio/mpeg' || file.name.endsWith('.mp3')) {
        setUploadedFile(file);
      } else {
        alert('Bitte nur MP3-Dateien hochladen!');
      }
    }
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files && files[0]) {
      const file = files[0];
      if (file.type === 'audio/mpeg' || file.name.endsWith('.mp3')) {
        setUploadedFile(file);
      } else {
        alert('Bitte nur MP3-Dateien hochladen!');
      }
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">MP3 Upload</h1>
          <p className="text-gray-300">Ziehe deine MP3-Datei hierher oder klicke zum Auswählen</p>
        </div>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-4 border-dashed rounded-2xl p-12
            transition-all duration-300 ease-in-out
            ${isDragging 
              ? 'border-emerald-500 bg-emerald-900/30 scale-105' 
              : 'border-gray-600 bg-slate-800/50 hover:border-emerald-600 hover:bg-slate-800/70'
            }
          `}
        >
          <input
            type="file"
            accept="audio/mpeg,.mp3"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            id="file-input"
          />

          {!uploadedFile ? (
            <div className="flex flex-col items-center justify-center text-center">
              <div className={`
                mb-6 p-6 rounded-full transition-all duration-300
                ${isDragging ? 'bg-emerald-700 scale-110' : 'bg-emerald-800'}
              `}>
                <Upload className="w-16 h-16 text-white" />
              </div>
              
              <h3 className="text-2xl font-semibold text-white mb-2">
                {isDragging ? 'Datei loslassen' : 'MP3-Datei hierher ziehen'}
              </h3>
              
              <p className="text-gray-400 mb-4">oder</p>
              
              <button
                onClick={() => document.getElementById('file-input').click()}
                className="px-6 py-3 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-lg transition-colors duration-200"
              >
                Datei auswählen
              </button>
              
              <p className="text-sm text-gray-500 mt-4">
                Nur MP3-Dateien werden akzeptiert
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-between bg-slate-700/50 rounded-lg p-6">
              <div className="flex items-center gap-4 flex-1">
                <div className="p-3 bg-emerald-700 rounded-lg">
                  <Music className="w-8 h-8 text-white" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h4 className="text-lg font-semibold text-white truncate">
                    {uploadedFile.name}
                  </h4>
                  <p className="text-sm text-gray-400">
                    {formatFileSize(uploadedFile.size)}
                  </p>
                </div>
              </div>

              <button
                onClick={removeFile}
                className="ml-4 p-2 hover:bg-red-500/20 rounded-lg transition-colors duration-200 group"
                title="Datei entfernen"
              >
                <X className="w-6 h-6 text-gray-400 group-hover:text-red-400" />
              </button>
            </div>
          )}
        </div>

        {uploadedFile && (
          <div className="mt-6 flex gap-4">
            <button
              onClick={() => {
                // Hier kannst du die Upload-Logik implementieren
                console.log('Uploading:', uploadedFile);
                alert(`Datei ${uploadedFile.name} wird hochgeladen...`);
              }}
              className="flex-1 px-6 py-3 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-lg transition-colors duration-200"
            >
              Hochladen
            </button>
            
            <button
              onClick={removeFile}
              className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors duration-200"
            >
              Abbrechen
            </button>
          </div>
        )}
      </div>
    </div>
  );
}