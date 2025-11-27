import { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
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
      .then((res) => res.json())
      .then((data) => setPhaseData(data));

    fetch("/tone_results.json")
      .then((res) => res.json())
      .then((data) => setToneData(data));

    fetch("/quality_results.json")
      .then((res) => res.json())
      .then((data) => setQualityData(data));

    fetch("/speakers_results.json")
      .then((res) => res.json())
      .then((data) => setSpeakerData(data));
  }, []);

  const getToneBarData = () => {
    if (!toneData) return [];
    const allTones = new Set<string>();
    Object.keys(toneData.red_arguments.tone).forEach((t) => allTones.add(t));
    Object.keys(toneData.blue_arguments.tone).forEach((t) => allTones.add(t));
    return Array.from(allTones).map((tone) => ({
      tone,
      rot: toneData.red_arguments.tone[tone]?.percentage || 0,
      blau: toneData.blue_arguments.tone[tone]?.percentage || 0
    }));
  };

  const getQualityStackedData = () => {
    if (!qualityData) return [];
    const allQualities = new Set<string>();
    Object.keys(qualityData.red_arguments.quality).forEach((q) => allQualities.add(q));
    Object.keys(qualityData.blue_arguments.quality).forEach((q) => allQualities.add(q));

    const redData: any = { player: "Spieler Rot" };
    const blueData: any = { player: "Spieler Blau" };

    allQualities.forEach((q) => {
      redData[q] = qualityData.red_arguments.quality[q]?.percentage || 0;
      blueData[q] = qualityData.blue_arguments.quality[q]?.percentage || 0;
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
    <div className="min-h-screen bg-gray-800 p-12 text-white overflow-x-hidden">
      <div className="max-w-7xl mx-auto mb-12 flex items-center justify-between">
        <button
          onClick={() => window.location.href = '/'}
          className="px-4 py-2 border-2 border-white rounded-lg text-white hover:bg-white hover:text-gray-800 transition-colors"
        >
          ← Zurück
        </button>
        <h1 className="text-4xl font-bold flex-1 text-center">
          Dashboard - Phasen Analyse
        </h1>
        <div className="w-[120px]"></div>
      </div>

      {/* ── Obere Reihe ── */}
      <div className="grid grid-cols-[3fr_2fr] gap-12 max-w-7xl mx-auto mb-12">
        {/* Oben links: Tone Chart */}
        <div className="flex flex-col h-[360px] border-2 border-white rounded-xl p-4">
          <h2 className="font-bold text-2xl mb-6 text-white">Tone: Spielerstimmung</h2>
          <div className="flex-1">
            {toneData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={getToneBarData()}
                  layout="vertical"
                  margin={{ top: 20, right: 20, bottom: 40, left: 20 }}
                >
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    tick={{ fill: "white" }}
                    axisLine={{ stroke: "white" }}
                    tickLine={{ stroke: "white" }}
                    label={{ value: "Prozent (%)", position: "insideBottom", fill: "white", offset: -10 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="tone"
                    width={120}
                    tick={{ fill: "white" }}
                    axisLine={{ stroke: "white" }}
                    tickLine={{ stroke: "white" }}
                  />
                  <Tooltip
                    formatter={(v: number) => `${v.toFixed(1)}%`}
                    contentStyle={{ backgroundColor: "#1f2937", color: "white", borderRadius: "4px" }}
                  />
                  <Legend verticalAlign="top" wrapperStyle={{ color: "white" }} />
                  <Bar dataKey="rot" fill="#DC0000" name="Spieler Rot" />
                  <Bar dataKey="blau" fill="#3B82F6" name="Spieler Blau" />
                </BarChart>
              </ResponsiveContainer>
            ) : <p>Lade Daten...</p>}
          </div>
        </div>

        {/* Oben rechts: Phasen */}
        <div className="flex flex-col overflow-auto h-[360px] border-2 border-white rounded-xl p-4">
          <h2 className="font-bold text-2xl mb-6 text-white">Phasen-Übersicht</h2>
          {phaseData ? (
            <div className="flex-1 overflow-auto">
              <div className="mb-6 p-4 bg-gray-700 rounded-lg">
                <p className="text-lg text-white">
                  <span className="font-semibold">Gesamtdauer:</span>{" "}
                  {phaseData.total_formatted}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {Object.entries(phaseData.phases).map(([phaseName, data], idx) => (
                  <div
                    key={phaseName}
                    className="p-5 rounded-lg border-l-4 overflow-hidden bg-gray-700"
                    style={{ borderLeftColor: colors[idx % colors.length] }}
                  >
                    <h3 className="font-bold text-lg mb-3 break-words text-white">{phaseName}</h3>
                    <p className="text-white">Dauer: {data.formatted}</p>
                    <p className="text-white">Anteil: {data.percentage.toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            </div>
          ) : <p>Lade Daten...</p>}
        </div>
      </div>

      {/* ── Untere Reihe ── */}
      <div className="grid grid-cols-[2fr_3fr] gap-12 max-w-7xl mx-auto">
        {/* Unten links: Quality Chart */}
        <div className="flex flex-col h-[320px] border-2 border-white rounded-xl p-4">
          <h2 className="font-bold text-2xl mb-6 text-white">Qualität der Argumente</h2>
          <div className="flex-1">
            {qualityData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={getQualityStackedData()}
                  margin={{ top: 30, right: 20, bottom: 20, left: 85 }}
                >
                  <XAxis 
                    type="category" 
                    dataKey="player"
                    tick={{ fill: "white" }}
                    axisLine={{ stroke: "white" }}
                    tickLine={{ stroke: "white" }}
                  />
                  <YAxis 
                    type="number" 
                    domain={[0, 100]}
                    tick={{ fill: "white" }}
                    axisLine={{ stroke: "white" }}
                    tickLine={{ stroke: "white" }}
                    label={{ value: "Prozent (%)", angle: -90, position: "center", fill: "white", dx: -25 }}
                  />
                  <Tooltip 
                    formatter={(v: number) => `${v.toFixed(1)}%`}
                    contentStyle={{ backgroundColor: "#1f2937", color: "white", borderRadius: "4px" }}
                  />
                  <Legend 
                    verticalAlign="top" 
                    wrapperStyle={{ color: "white", paddingBottom: "20px" }}
                    payload={[
                      { value: "Stark", type: "rect", color: "#10B981" },
                      { value: "Mittel", type: "rect", color: "#F59E0B" },
                      { value: "Schwach", type: "rect", color: "#EF4444" }
                    ]}
                  />
                  <Bar dataKey="stark" stackId="a" fill="#10B981" name="Stark" />
                  <Bar dataKey="mittel" stackId="a" fill="#F59E0B" name="Mittel" />
                  <Bar dataKey="schwach" stackId="a" fill="#EF4444" name="Schwach" />
                </BarChart>
              </ResponsiveContainer>
            ) : <p>Lade Daten...</p>}
          </div>
        </div>

        {/* Unten rechts: Speaker Chart */}
        <div className="flex flex-col h-[320px] border-2 border-white rounded-xl p-4">
          <h2 className="font-bold text-2xl mb-6 text-white">Redeanteile der Speaker</h2>
          <div className="flex-1">
            {speakerData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={getSpeakerStackedData()} 
                  layout="vertical"
                  margin={{ top: 20, right: 20, bottom: 50, left: 20 }}
                  barSize={40}
                >
                  <XAxis 
                    type="number" 
                    domain={[0, 100]}
                    tick={{ fill: "white" }}
                    axisLine={{ stroke: "white" }}
                    tickLine={{ stroke: "white" }}
                    label={{ value: "Prozent (%)", position: "insideBottom", fill: "white", offset: -35 }}
                  />
                  <YAxis 
                    type="category" 
                    dataKey="label" 
                    hide 
                  />
                  <Tooltip 
                    formatter={(v: number) => `${v.toFixed(1)}%`}
                    contentStyle={{ backgroundColor: "#1f2937", color: "white", borderRadius: "4px" }}
                  />
                  <Legend verticalAlign="top" wrapperStyle={{ color: "white" }} />
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