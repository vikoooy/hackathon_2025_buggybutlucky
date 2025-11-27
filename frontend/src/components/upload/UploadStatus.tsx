interface Props {
  status: string;
  progress: number;
}

export function UploadStatus({ status, progress }: Props) {
  return (
    <div className="mt-4 bg-gray-800 p-4 rounded-lg text-white">
      <p>Status: {status}</p>

      {(status === "uploading" || status === "processing") && (
        <div className="mt-2">
          <div className="w-full h-3 bg-gray-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-red-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="mt-1 text-sm text-gray-400">{progress}%</p>
        </div>
      )}
    </div>
  );
}
