import { useState } from "react";

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

  return (
    <div>
      <input
        type="file"
        accept="audio/*"
        onChange={(e) => {
          setFile(e.target.files?.[0] ?? null);
          setStatus("idle");
        }}
      />

      <button
        onClick={handleUpload}
        disabled={!file || status === "uploading" || status === "processing"}
      >
        Upload
      </button>

      <div>Status: {status}</div>
      <div>Progress: {progress}%</div>
    </div>
  );
}
