import { useState } from "react";
import { PieChart, Pie, Cell } from "recharts";

export function DashboardPage() {
  const [selectedPlayer, setSelectedPlayer] = useState("player1");

  // Dummy Pie Data
  const data = [
    { name: "A", value: 40 },
    { name: "B", value: 25 },
    { name: "C", value: 20 },
    { name: "D", value: 15 },
  ];

  const colors = ["#4F46E5", "#EC4899", "#10B981", "#F59E0B"];

  return (
    <div className="min-h-screen bg-[#949494] p-12 text-black">
      <h1 className="text-4xl font-bold text-center mb-12">
        Dashboard
      </h1>

      <div className="grid grid-cols-3 gap-12 max-w-6xl mx-auto">

        {/* 🟦 LINKS: zwei große Boxen */}
        <div className="col-span-1 flex flex-col gap-6">
          <div className="bg-white rounded-xl p-6 h-56 shadow-md">
            <h2 className="font-bold mb-2">Box 1</h2>
            <p className="text-gray-700">Inhalt folgt…</p>
          </div>

          <div className="bg-white rounded-xl p-6 h-56 shadow-md">
            <h2 className="font-bold mb-2">Box 2</h2>
            <p className="text-gray-700">Inhalt folgt…</p>
          </div>
        </div>

        {/* 🟧 MITTE: Kreisdiagramm */}
        <div className="col-span-1 flex justify-center items-center">
          <PieChart width={260} height={260}>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              outerRadius={120}
              dataKey="value"
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={colors[i]} />
              ))}
            </Pie>
          </PieChart>
        </div>

        {/* 🟩 RECHTS: Player-Auswahl */}
        <div className="col-span-1 flex flex-col justify-center gap-4 pl-4">
          <label className="flex items-center gap-2 text-lg">
            <input
              type="radio"
              name="player"
              value="player1"
              checked={selectedPlayer === "player1"}
              onChange={() => setSelectedPlayer("player1")}
            />
            Player 1
          </label>

          <label className="flex items-center gap-2 text-lg">
            <input
              type="radio"
              name="player"
              value="player2"
              checked={selectedPlayer === "player2"}
              onChange={() => setSelectedPlayer("player2")}
            />
            Player 2
          </label>

          <label className="flex items-center gap-2 text-lg">
            <input
              type="radio"
              name="player"
              value="mod"
              checked={selectedPlayer === "mod"}
              onChange={() => setSelectedPlayer("mod")}
            />
            Mod
          </label>
        </div>
      </div>

      {/* 🟡 UNTEN: Emojis */}
      <div className="flex justify-center gap-12 mt-16">
        <button className="w-20 h-20 rounded-full bg-white shadow-md flex items-center justify-center text-3xl">
          🙂
        </button>
        <button className="w-20 h-20 rounded-full bg-white shadow-md flex items-center justify-center text-3xl">
          😐
        </button>
        <button className="w-20 h-20 rounded-full bg-white shadow-md flex items-center justify-center text-3xl">
          🙁
        </button>
      </div>
    </div>
  );
}
