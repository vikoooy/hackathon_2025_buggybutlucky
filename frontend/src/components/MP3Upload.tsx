import React, { useState } from 'react';
import { Upload, Music } from 'lucide-react';

export default function MP3Upload() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [profileImage, setProfileImage] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
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

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
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

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setProfileImage(e.target?.result as string);
        };
        reader.readAsDataURL(file);
      } else {
        alert('Bitte nur Bilddateien hochladen!');
      }
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 p-8">
      {/* Header mit Bild und Titel */}
      <div className="flex items-center gap-6 mb-12">
        {/* Rundes Profilbild */}
        <div className="relative">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            id="image-input"
          />
          <div className="w-24 h-24 rounded-full bg-slate-700 border-4 border-emerald-600 overflow-hidden hover:border-emerald-500 transition-colors cursor-pointer">
            {profileImage ? (
              <img src={profileImage} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm text-center p-2">
                Bild hochladen
              </div>
            )}
          </div>
        </div>

        {/* Titel Input */}
        <div className="flex-1">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Projekttitel eingeben..."
            className="w-full max-w-md px-4 py-3 bg-slate-800/70 border-2 border-gray-600 rounded-lg text-white text-xl font-semibold placeholder-gray-500 focus:outline-none focus:border-emerald-600 transition-colors"
          />
        </div>
      </div>

      {/* Hauptbereich: Upload links, Rest rechts */}
      <div className="grid grid-cols-3 gap-8">
        {/* Linkes Drittel: Upload */}
        <div className="col-span-1">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">MP3 Upload</h2>
            <p className="text-gray-300 text-sm">Ziehe deine MP3-Datei hierher</p>
          </div>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              relative border-4 border-dashed rounded-2xl p-8
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
                  mb-4 p-4 rounded-full transition-all duration-300
                  ${isDragging ? 'bg-emerald-700 scale-110' : 'bg-emerald-800'}
                `}>
                  <Upload className="w-12 h-12 text-white" />
                </div>
                
                <h3 className="text-lg font-semibold text-white mb-2">
                  {isDragging ? 'Loslassen' : 'MP3 ziehen'}
                </h3>
                
                <p className="text-gray-400 text-sm mb-3">oder</p>
                
                <button
                  onClick={() => document.getElementById('file-input')?.click()}
                  className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-semibold rounded-lg transition-colors duration-200"
                >
                  Datei wählen
                </button>
                
                <p className="text-xs text-gray-500 mt-3">
                  Nur MP3-Dateien
                </p>
              </div>
            ) : (
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-emerald-700 rounded-lg">
                    <Music className="w-6 h-6 text-white" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-white truncate">
                      {uploadedFile.name}
                    </h4>
                    <p className="text-xs text-gray-400">
                      {formatFileSize(uploadedFile.size)}
                    </p>
                  </div>
                </div>

                <button
                  onClick={removeFile}
                  className="w-full px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm rounded-lg transition-colors duration-200"
                >
                  Entfernen
                </button>
              </div>
            )}
          </div>

          {uploadedFile && (
            <div className="mt-4">
              <button
                onClick={() => {
                  console.log('Uploading:', uploadedFile);
                  alert(`Datei ${uploadedFile.name} wird hochgeladen...`);
                }}
                className="w-full px-4 py-3 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-lg transition-colors duration-200"
              >
                Hochladen
              </button>
            </div>
          )}
        </div>

        {/* Rechte zwei Drittel: Platz für weitere Inhalte */}
        <div className="col-span-2">
          <div className="bg-slate-800/50 border-2 border-gray-700 rounded-2xl p-8 h-full">
            <h3 className="text-xl font-bold text-white mb-4">Weitere Inhalte</h3>
            <p className="text-gray-400">
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
