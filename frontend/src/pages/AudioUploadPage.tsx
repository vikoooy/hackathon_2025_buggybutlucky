import { useState } from "react";
import { UploadZone } from "../components/upload/UploadZone";
import { FileCard } from "../components/upload/FileCard";
import { UploadStatus } from "../components/upload/UploadStatus";
import { useAudioUpload } from "../hooks/useAudioUpload";
import { useNavigate } from "react-router-dom";

export function AudioUploadPage() {
  const { file, setFile, status, progress, removeFile, handleUpload } = useAudioUpload();
  const [isDragging, setIsDragging] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 p-12">
      <div className="grid grid-cols-3 gap-16 max-w-6xl mx-auto min-h-[80vh]">
        
        {/* Upload-Bereich mittig */}
        <div className="col-span-1 flex items-center justify-center">
          <div className="w-full max-w-sm">
            {!file ? (
              <UploadZone
                onFileSelect={setFile}
                isDragging={isDragging}
                setIsDragging={setIsDragging}
              />
            ) : (
              <>
                <FileCard file={file} onRemove={removeFile} />
                <button
                  className="mt-4 w-full py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-semibold transition"
                  onClick={handleUpload}
                  disabled={status === "uploading" || status === "processing"}
                >
                  {status === "uploading"
                    ? "Hochladen…"
                    : status === "processing"
                    ? "Verarbeitung…"
                    : "Upload starten"}
                </button>

                <UploadStatus status={status} progress={progress} />
              </>
            )}
          </div>
        </div>

        {/* Rechte zwei Drittel – Buttons */}
        <div className="col-span-2 flex flex-col justify-center gap-6">
          <button
            className="h-24 bg-transparent border-2 border-white text-white text-lg font-semibold rounded-lg hover:bg-white/10 transition"
            onClick={() => navigate("/dashboard")}
          >
            View Dashboard
          </button>

          <button
            className="h-24 bg-transparent border-2 border-white text-white text-lg font-semibold rounded-lg hover:bg-white/10 transition"
            onClick={() => navigate("/report")}
          >
            Report
          </button>

          <button
            className="h-24 bg-transparent border-2 border-white text-white text-lg font-semibold rounded-lg hover:bg-white/10 transition"
            onClick={() => navigate("/view-x")}
          >
            View X
          </button>
        </div>
      </div>
    </div>
  );
}
