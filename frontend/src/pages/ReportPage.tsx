export function ReportPage() {
  const handleDownload = async () => {
    const res = await fetch("/report/generate", {
      method: "POST",
    });

    if (!res.ok) {
      alert("Fehler beim Generieren des Reports");
      return;
    }

    // PDF Blob empfangen
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    // Download starten
    const a = document.createElement("a");
    a.href = url;
    a.download = "wargaming_report.pdf";
    a.click();

    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-900 p-10 text-white flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-6">Report</h1>

      <button
        onClick={handleDownload}
        className="px-8 py-4 bg-red-500 hover:bg-red-600 rounded-xl text-white font-semibold shadow-lg"
      >
        PDF Report generieren & herunterladen
      </button>
    </div>
  );
}
