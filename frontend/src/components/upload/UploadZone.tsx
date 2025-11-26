import { Upload } from "lucide-react";

interface Props {
  onFileSelect: (file: File) => void;
  isDragging: boolean;
  setIsDragging: (v: boolean) => void;
}

export function UploadZone({ onFileSelect, isDragging, setIsDragging }: Props) {
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center transition 
        ${
          isDragging
            ? "border-red-500 bg-red-900/20"
            : "border-gray-600 bg-[#0E1621]"
        }
      `}
    >
      <input
        type="file"
        accept="audio/*"
        onChange={handleFileInput}
        className="hidden"
        id="file-input"
      />

      <div className="flex flex-col items-center gap-4">
        <div className="p-4 bg-red-600 rounded-full">
          <Upload className="w-10 h-10 text-white" />
        </div>

        <h3 className="text-white font-semibold text-lg">Audio-Datei hochladen</h3>
        <p className="text-gray-300 text-sm">Drag & Drop oder Datei wählen</p>

        <button
          onClick={() => document.getElementById("file-input")?.click()}
          className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
        >
          Datei wählen
        </button>
      </div>
    </div>
  );
}
