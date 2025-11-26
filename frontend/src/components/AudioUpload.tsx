import { useState } from "react";
import { Upload, Music } from "lucide-react";
import profileImage from "../assets/profile.jpg";

type JobStatus = "idle" | "uploading" | "processing" | "done" | "error";

interface UploadResponse {
  status: string;
  job_id: string;
  filename: string;
}

interface ProgressResponse {
  status: "in_progress" | "completed" | "failed";
  progress: number;
  filename: string;
  error?: string;
}

export default function AudioUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<JobStatus>("idle");
  const [progress, setProgress] = useState<number>(0);
  const [isDragging, setIsDragging] = useState(false);

  async function handleUpload(): Promise<void> {
    try {
      if (!file) return;

      setStatus("uploading");

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/audio/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data: UploadResponse = await res.json();

      setStatus("processing");
      await pollProgress(data.job_id);

    } catch (error) {
      console.error(error);
      setStatus("error");
    }
  }

  async function pollProgress(jobId: string): Promise<void> {
    let done = false;

    while (!done) {
      const res = await fetch(`/audio/progress/${jobId}`);

      if (!res.ok) {
        setStatus("error");
        return;
      }

      const data: ProgressResponse = await res.json();
      setProgress(data.progress);

      if (data.status === "completed") {
        setStatus("done");
        done = true;
      } else if (data.status === "failed") {
        setStatus("error");
        done = true;
      } else {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
  }

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
      setFile(files[0]);
      setStatus("idle");
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      setFile(files[0]);
      setStatus("idle");
    }
  };

  const removeFile = () => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 p-8">
      {/* Header mit Bild und Titel */}
      <div className="flex items-center gap-6 mb-12">
        {/* Rundes Profilbild */}
        <div className="relative">
          <div className="w-24 h-24 rounded-full bg-slate-700 border-4 border-emerald-600 overflow-hidden">
            <img
              src={profileImage}
              alt="Profile"
              className="w-full h-full object-cover"
            />
          </div>
        </div>

        {/* Titel */}
        <div className="flex-1">
          <h1 className="w-full px-4 py-6 bg-slate-800/70 border-2 border-gray-600 rounded-lg text-white text-3xl font-semibold text-center">
            Audio Upload & Transkription
          </h1>
        </div>
      </div>

      {/* Hauptbereich: Upload links, Rest rechts */}
      <div className="grid grid-cols-3 gap-8 max-w-7xl mx-auto min-h-[calc(100vh-200px)]">
        {/* Linkes Drittel: Upload */}
        <div className="col-span-1 flex items-center">
          <div className="w-full">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">
                Audio Upload
              </h2>
              <p className="text-gray-300 text-sm">
                Ziehe deine Audio-Datei hierher
              </p>
            </div>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                relative border-4 border-dashed rounded-2xl p-8
                transition-all duration-300 ease-in-out
                ${
                  isDragging
                    ? "border-emerald-500 bg-emerald-900/30 scale-105"
                    : "border-gray-600 bg-slate-800/50 hover:border-emerald-600 hover:bg-slate-800/70"
                }
              `}
            >
              <input
                type="file"
                accept="audio/*"
                onChange={handleFileInput}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                id="file-input"
              />

              {!file ? (
                <div className="flex flex-col items-center justify-center text-center">
                  <div
                    className={`
                      mb-4 p-4 rounded-full transition-all duration-300
                      ${isDragging ? "bg-emerald-700 scale-110" : "bg-emerald-800"}
                    `}
                  >
                    <Upload className="w-12 h-12 text-white" />
                  </div>

                  <h3 className="text-lg font-semibold text-white mb-2">
                    {isDragging ? "Loslassen" : "Audio-Datei ziehen"}
                  </h3>

                  <p className="text-gray-400 text-sm mb-3">oder</p>

                  <button
                    onClick={() =>
                      document.getElementById("file-input")?.click()
                    }
                    className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-semibold rounded-lg transition-colors duration-200"
                  >
                    Datei wählen
                  </button>

                  <p className="text-xs text-gray-500 mt-3">
                    Alle Audio-Formate
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
                        {file.name}
                      </h4>
                      <p className="text-xs text-gray-400">
                        {formatFileSize(file.size)}
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

            {file && (
              <div className="mt-4">
                <button
                  onClick={handleUpload}
                  disabled={
                    status === "uploading" || status === "processing"
                  }
                  className="w-full px-4 py-3 bg-emerald-700 hover:bg-emerald-800 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors duration-200"
                >
                  {status === "uploading"
                    ? "Hochladen..."
                    : status === "processing"
                    ? "Verarbeitung..."
                    : "Hochladen"}
                </button>
              </div>
            )}

            {/* Status und Progress */}
            {status !== "idle" && (
              <div className="mt-4 bg-slate-800/70 rounded-lg p-4">
                <div className="text-white text-sm mb-2">
                  Status: <span className="font-semibold">{status}</span>
                </div>
                {(status === "processing" || status === "uploading") && (
                  <div className="text-white text-sm">
                    Progress: <span className="font-semibold">{progress}%</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Rechte zwei Drittel: Button-Bereich */}
        <div className="col-span-2 flex flex-col gap-4 w-full justify-center">
          <button className="w-full h-24 bg-transparent border-2 border-white hover:bg-white/10 text-white text-lg font-semibold rounded-lg transition-colors duration-200">
            Button 1
          </button>
          <button className="w-full h-24 bg-transparent border-2 border-white hover:bg-white/10 text-white text-lg font-semibold rounded-lg transition-colors duration-200">
            Button 2
          </button>
          <button className="w-full h-24 bg-transparent border-2 border-white hover:bg-white/10 text-white text-lg font-semibold rounded-lg transition-colors duration-200">
            Button 3
          </button>
        </div>
      </div>
    </div>
  );
}
