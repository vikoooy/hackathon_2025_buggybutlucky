import { jsPDF } from "jspdf";

export function generatePdfReport() {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text("Audio Processing Report", 10, 20);

  doc.setFontSize(12);
  doc.text("Dieser Report wurde automatisch erzeugt.", 10, 35);

  doc.text(
    "Hier kannst du später dynamische Informationen einfügen,\n" +
      "z. B. Ergebnisse, Interpretation, Metadaten, Transkript-Auszug.\n",
    10,
    50
  );

  // PDF als Download ausgeben
  doc.save("report.pdf");
}
