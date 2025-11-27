import { useState } from "react";
import { UploadZone } from "../components/upload/UploadZone";
import { FileCard } from "../components/upload/FileCard";
import { UploadStatus } from "../components/upload/UploadStatus";
import { useAudioUpload } from "../hooks/useAudioUpload";
import { useNavigate } from "react-router-dom";
import { generatePdfReport } from "../lib/generateReport";

export function AudioUploadPage() {
  const { file, setFile, status, progress, removeFile, handleUpload } = useAudioUpload();
  const [isDragging, setIsDragging] = useState(false);
  const navigate = useNavigate();

return (
  <div
    className="
      min-h-screen 
      text-white 
      bg-gradient-to-br 
      from-[#2A2F3A] 
      via-[#1A1D23] 
      to-[#0F1115] 
      flex 
      flex-col 
      items-center 
      justify-center
      px-12
    "
  >

    {/* Header */}
    <div className="mb-20 flex justify-center">
      <div
        className="
          backdrop-blur-2xl
          bg-white/10
          border border-white/20
          px-16 py-6
          rounded-3xl
          shadow-[0_8px_32px_rgba(0,0,0,0.4)]
        "
      >
        <h1 className="text-4xl font-bold tracking-wide text-white">
          Wargaming Report Portal
        </h1>
      </div>
    </div>

    {/* 2-Spalten Layout */}
    <div className="grid grid-cols-3 gap-16 max-w-6xl w-full">

      {/* Upload Box (linke Spalte) */}
      <div className="col-span-1 flex items-center justify-center">
        <div
          className="
            w-full max-w-sm
            backdrop-blur-2xl
            bg-white/10
            border border-white/20
            rounded-3xl
            shadow-[0_8px_32px_rgba(0,0,0,0.4)]
            hover:bg-white/15
            transition
            p-8
          "
        >
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
                className="
                  mt-4 w-full py-3
                  bg-[#D64545]
                  hover:bg-[#B73737]
                  rounded-xl
                  text-white font-semibold
                  shadow-lg shadow-[rgba(214,69,69,0.35)]
                  transition
                "
                onClick={handleUpload}
                disabled={status === 'uploading' || status === 'processing'}
              >
                {status === 'uploading'
                  ? 'Hochladen…'
                  : status === 'processing'
                  ? 'Verarbeitung…'
                  : 'Upload starten'}
              </button>

              <UploadStatus status={status} progress={progress} />
            </>
          )}
        </div>
      </div>

      {/* Buttons rechts – jetzt nur 2 und vertikal aligned */}
      <div className="col-span-2 flex flex-col justify-center gap-8 pr-4">

        {/* View Dashboard */}
        <button
          className="
            h-24
            backdrop-blur-2xl
            bg-white/10
            border border-white/20
            rounded-3xl
            shadow-[0_8px_32px_rgba(0,0,0,0.35)]
            hover:bg-white/15
            text-white
            text-xl
            font-semibold
            transition
          "
          onClick={() => navigate('/dashboard')}
        >
          View Dashboard
        </button>

        {/* Report */}
        <button
          className="
            h-24
            backdrop-blur-2xl
            bg-white/10
            border border-white/20
            rounded-3xl
            shadow-[0_8px_32px_rgba(0,0,0,0.35)]
            hover:bg-white/15
            text-white
            text-xl
            font-semibold
            transition
          "
          onClick={generatePdfReport}
        >
          Report
        </button>

      </div>
    </div>
  </div>
);

}
