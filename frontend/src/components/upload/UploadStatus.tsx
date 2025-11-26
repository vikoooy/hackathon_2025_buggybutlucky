export function UploadStatus({
  status,
  progress,
}: {
  status: string;
  progress: number;
}) {
  if (status === "idle") return null;

  return (
    <div className="mt-6 bg-slate-800/70 p-4 rounded-lg border border-slate-700">
      <p className="text-white text-sm mb-2">
        Status: <span className="font-semibold">{status}</span>
      </p>

      {(status === "processing" || status === "uploading") && (
        <p className="text-white text-sm">
          Fortschritt: <span className="font-semibold">{progress}%</span>
        </p>
      )}
    </div>
  );
}
