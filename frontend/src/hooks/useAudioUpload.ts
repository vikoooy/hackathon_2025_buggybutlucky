import { useState } from "react";

export type JobStatus = "idle" | "uploading" | "processing" | "done" | "error";

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

// Falls du später eine .env verwendest, kannst du das hier variabler machen.
const API_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useAudioUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<JobStatus>("idle");
  const [progress, setProgress] = useState<number>(0);

  const removeFile = () => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
  };

  async function handleUpload(): Promise<void> {
    try {
      if (!file) return;

      setStatus("uploading");
      setProgress(0);

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/audio/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        console.error("Upload failed:", await res.text());
        throw new Error("Upload failed");
      }

      const data: UploadResponse = await res.json();

      setStatus("processing");
      await pollProgress(data.job_id);

    } catch (err) {
      console.error("Upload error:", err);
      setStatus("error");
    }
  }

  async function pollProgress(jobId: string): Promise<void> {
    let done = false;

    while (!done) {
      try {
        const res = await fetch(`${API_BASE}/audio/progress/${jobId}`);

        if (!res.ok) {
          console.error("Progress failed:", await res.text());
          setStatus("error");
          return;
        }

        const data: ProgressResponse = await res.json();
        setProgress(data.progress ?? 0);

        if (data.status === "completed") {
          setStatus("done");
          done = true;
        } else if (data.status === "failed") {
          setStatus("error");
          done = true;
        } else {
          await new Promise((r) => setTimeout(r, 1000));
        }
      } catch (err) {
        console.error("Polling error:", err);
        setStatus("error");
        return;
      }
    }
  }

  return {
    file,
    setFile,
    status,
    progress,
    removeFile,
    handleUpload,
  };
}
