import { X } from "lucide-react";

interface FileCardProps {
  file: File;
  onRemove: () => void;
}

export function FileCard({ file, onRemove }: FileCardProps) {
  return (
    <div
      className="
        relative
        bg-white/10 
        backdrop-blur-xl 
        border border-white/20 
        rounded-2xl 
        shadow-lg 
        p-5
        flex
        flex-col
        gap-2
        overflow-hidden   /* wichtig! */
      "
    >
      {/* X Button */}
      <button
        onClick={onRemove}
        className="
          absolute 
          top-3 
          right-3
          bg-red-600 
          hover:bg-red-700 
          text-white 
          p-2 
          rounded-xl 
          transition 
          shadow-md
          z-20
        "
      >
        <X size={18} />
      </button>

      {/* File Info Row */}
      <div className="flex items-center gap-3 pr-12">
        <span className="text-red-400 text-2xl">🎵</span>

        <div className="flex flex-col">
          <span className="font-semibold text-white truncate max-w-[240px]">
            {file.name}
          </span>
          <span className="text-gray-300 text-sm">
            {(file.size / (1024 * 1024)).toFixed(2)} MB
          </span>
        </div>
      </div>
    </div>
  );
}
