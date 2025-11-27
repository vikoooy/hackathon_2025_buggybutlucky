import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AudioUploadPage } from "./pages/AudioUploadPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ReportPage } from "./pages/ReportPage";
import { ViewXPage } from "./pages/ViewXPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AudioUploadPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/view-x" element={<ViewXPage />} />
      </Routes>
    </BrowserRouter>
  );
}
