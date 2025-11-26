import { Upload } from "lucide-react";

interface Props {
  onFileSelect: (file: File) => void;
  isDragging: boolean;
  setIsDragging: (b: boolean) => void;
}

export function UploadZone({ onFileSelect, isDragging, setIsDragging }: Props) {
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) onFileSelect(e.target.files[0]);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) onFileSelect(f);
    setIsDragging(false);
  };

  return (
    <div
      className={`
        border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
        transition-all duration-300 bg-slate-900/40
        hover:bg-slate-900/70 hover:border-emerald-500
        ${isDragging ? "border-emerald-500 bg-emerald-900/20 scale-[1.02]" : "border-slate-700"}
      `}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setIsDragging(false);
      }}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept="audio/*"
        onChange={handleFileInput}
        className="hidden"
        id="audio-file"
      />

      <div
        className="w-24 h-24 mx-auto mb-6 rounded-full bg-emerald-800/60 flex items-center justify-center"
        onClick={() => document.getElementById("audio-file")?.click()}
      >
        <Upload className="w-12 h-12 text-white" />
      </div>

      <p className="text-white text-lg font-semibold">Audio-Datei hochladen</p>
      <p className="text-gray-400 text-sm mt-2">Drag & Drop oder Datei wählen</p>
    </div>
  );
}
