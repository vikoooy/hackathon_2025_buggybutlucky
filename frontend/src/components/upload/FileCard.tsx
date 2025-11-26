import { Music } from "lucide-react";

export function FileCard({ file, onRemove }: { file: File; onRemove: () => void }) {
  return (
    <div className="bg-slate-800/70 rounded-lg p-5 shadow-lg border border-slate-700">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-emerald-700 rounded-lg">
          <Music className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-white font-semibold">{file.name}</p>
          <p className="text-gray-400 text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
        </div>
      </div>

      <button
        className="mt-4 w-full py-2 rounded-lg bg-red-700/20 hover:bg-red-700/30 text-red-300 transition"
        onClick={onRemove}
      >
        Entfernen
      </button>
    </div>
  );
}
