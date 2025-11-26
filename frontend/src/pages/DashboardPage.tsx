import { useState, useEffect } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Legend
} from "recharts";

interface PhaseData {
  total_seconds: number;
  total_formatted: string;
  phases: {
    [key: string]: {
      seconds: number;
      formatted: string;
      percentage: number;
    };
  };
}

interface ToneData {
  red_arguments: {
    total: number;
    tone: {
      [key: string]: {
        count: number;
        percentage: number;
      };
    };
  };
  blue_arguments: {
    total: number;
    tone: {
      [key: string]: {
        count: number;
        percentage: number;
      };
    };
  };
}

interface QualityData {
  red_arguments: {
    total: number;
    quality: {
      [key: string]: {
        count: number;
        percentage: number;
      };
    };
  };
  blue_arguments: {
    total: number;
    quality: {
      [key: string]: {
        count: number;
        percentage: number;
      };
    };
  };
}

interface SpeakerData {
  total_seconds: number;
  speakers: {
    [key: string]: {
      seconds: number;
      percentage: number;
    };
  };
}

export function DashboardPage() {
  const [phaseData, setPhaseData] = useState<PhaseData | null>(null);
  const [toneData, setToneData] = useState<ToneData | null>(null);
  const [qualityData, setQualityData] = useState<QualityData | null>(null);
  const [speakerData, setSpeakerData] = useState<SpeakerData | null>(null);

  useEffect(() => {
    fetch("/phases_results.json")
      .then((response) => response.json())
      .then((data) => setPhaseData(data));

    fetch("/tone_results.json")
      .then((response) => response.json())
      .then((data) => setToneData(data));

    fetch("/quality_results.json")
      .then((response) => response.json())
      .then((data) => setQualityData(data));

    fetch("/speakers_results.json")
      .then((response) => response.json())
      .then((data) => setSpeakerData(data));
  }, []);

  const getToneBarData = () => {
    if (!toneData) return [];

    const allTones = new Set<string>();
    Object.keys(toneData.red_arguments.tone).forEach((tone) => allTones.add(tone));
    Object.keys(toneData.blue_arguments.tone).forEach((tone) => allTones.add(tone));

    return Array.from(allTones).map((tone) => ({
      tone,
      rot: toneData.red_arguments.tone[tone]?.percentage || 0,
      blau: toneData.blue_arguments.tone[tone]?.percentage || 0
    }));
  };

  const getQualityStackedData = () => {
    if (!qualityData) return [];

    const allQualities = new Set<string>();
    Object.keys(qualityData.red_arguments.quality).forEach((quality) =>
      allQualities.add(quality)
    );
    Object.keys(qualityData.blue_arguments.quality).forEach((quality) =>
      allQualities.add(quality)
    );

    const redData: any = { player: "Spieler Rot" };
    const blueData: any = { player: "Spieler Blau" };

    allQualities.forEach((quality) => {
      redData[quality] = qualityData.red_arguments.quality[quality]?.percentage || 0;
      blueData[quality] = qualityData.blue_arguments.quality[quality]?.percentage || 0;
    });

    return [redData, blueData];
  };

  const getSpeakerStackedData = () => {
    if (!speakerData) return [];

    const data: any = { label: "Redeanteile" };

    Object.entries(speakerData.speakers).forEach(([speaker, info]) => {
      data[speaker] = info.percentage;
    });

    return [data];
  };

  const colors = ["#4F46E5", "#EC4899", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4", "#F97316"];
  const qualityColors: { [key: string]: string } = {
    stark: "#10B981",
    mittel: "#F59E0B",
    schwach: "#EF4444"
  };

  const speakerColors = ["#8B5CF6", "#EC4899", "#06B6D4"];

  return (
    <div className="min-h-screen bg-[#949494] p-12 text-black overflow-x-hidden">
      <h1 className="text-4xl font-bold text-center mb-12">
        Dashboard - Phasen Analyse
      </h1>

      {/* 2x2 GRID (alle Boxen gleiche Höhe) */}
      <div className="grid grid-cols-2 gap-12 max-w-7xl mx-auto auto-rows-fr">

        {/* ──────────────────────────────── */}
        {/* OBERES LINKES FELD: TONE CHART */}
        {/* ──────────────────────────────── */}
        <div className="bg-white rounded-xl p-6 shadow-md flex flex-col">
          <h2 className="font-bold mb-4">Tone-Verteilung: Rot vs Blau</h2>
          <div className="flex-1">
            {toneData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getToneBarData()} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="tone" width={120} />
                  <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                  <Legend />
                  <Bar dataKey="rot" fill="#EF4444" name="Spieler Rot" />
                  <Bar dataKey="blau" fill="#3B82F6" name="Spieler Blau" />
                </BarChart>
              </ResponsiveContainer>
            ) : <p>Lade Daten...</p>}
          </div>
        </div>

        {/* ──────────────────────────────── */}
        {/* OBERES RECHTES FELD: PHASEN */}
        {/* ──────────────────────────────── */}
        <div className="bg-white rounded-xl p-6 shadow-md flex flex-col overflow-auto">
          <h2 className="font-bold text-2xl mb-6">Phasen-Übersicht</h2>
          {phaseData ? (
            <div className="flex-1 overflow-auto">
              <div className="mb-6 p-4 bg-gray-100 rounded-lg">
                <p className="text-lg">
                  <span className="font-semibold">Gesamtdauer:</span>{" "}
                  {phaseData.total_formatted} ({phaseData.total_seconds}s)
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {Object.entries(phaseData.phases).map(([phaseName, data], idx) => (
                  <div
                    key={phaseName}
                    className="p-5 rounded-lg shadow-sm border-l-4"
                    style={{ borderLeftColor: colors[idx % colors.length] }}
                  >
                    <h3 className="font-bold text-lg mb-3">{phaseName}</h3>
                    <p>Dauer: {data.formatted}</p>
                    <p>Sekunden: {data.seconds}s</p>
                    <p>Anteil: {data.percentage.toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            </div>
          ) : <p>Lade Daten...</p>}
        </div>

        {/* ──────────────────────────────── */}
        {/* UNTEN LINKS: QUALITY CHART  */}
        {/* ──────────────────────────────── */}
        <div className="bg-white rounded-xl p-6 shadow-md flex flex-col">
          <h2 className="font-bold mb-4">Quality-Verteilung (Stacked)</h2>
          <div className="flex-1">
            {qualityData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getQualityStackedData()}>
                  <XAxis type="category" dataKey="player" />
                  <YAxis type="number" domain={[0, 100]} />
                  <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                  <Legend />
                  {Object.keys(qualityData.red_arguments.quality).map((quality, idx) => (
                    <Bar
                      key={quality}
                      dataKey={quality}
                      stackId="a"
                      fill={qualityColors[quality] || colors[idx % colors.length]}
                      name={quality}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            ) : <p>Lade Daten...</p>}
          </div>
        </div>

        {/* ──────────────────────────────── */}
        {/* UNTEN RECHTS: SPEAKER CHART */}
        {/* ──────────────────────────────── */}
        <div className="bg-white rounded-xl p-6 shadow-md flex flex-col">
          <h2 className="font-bold mb-4">Redeanteile der Speaker</h2>
          <div className="flex-1">
            {speakerData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getSpeakerStackedData()} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="label" hide />
                  <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                  <Legend />
                  {Object.keys(speakerData.speakers).map((speaker, idx) => (
                    <Bar
                      key={speaker}
                      dataKey={speaker}
                      stackId="a"
                      fill={speakerColors[idx % speakerColors.length]}
                      name={speaker}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            ) : <p>Lade Daten...</p>}
          </div>
        </div>

      </div>
    </div>
  );
}
