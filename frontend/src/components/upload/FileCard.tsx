import { Music, X } from "lucide-react";

interface Props {
  file: File;
  onRemove: () => void;
}

export function FileCard({ file, onRemove }: Props) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg text-white flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Music className="w-6 h-6 text-red-500" />
        <div>
          <p className="font-semibold">{file.name}</p>
          <p className="text-gray-400 text-sm">
            {(file.size / 1024 / 1024).toFixed(2)} MB
          </p>
        </div>
      </div>

      <button
        onClick={onRemove}
        className="p-2 rounded-md bg-red-600 hover:bg-red-700 text-white"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
