"use client";

import { useMemo } from "react";
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter } from "recharts";
import { TrendingUp, TrendingDown } from "lucide-react";

const SpreadMonitor = () => {
  const spreadData = useMemo(() => {
    const months = 24;
    const data = [];
    for (let i = 0; i < months; i++) {
      const base = 200 + Math.sin(i / 6) * 50;
      data.push({
        month: `M${i + 1}`,
        cloAAA: base + 20 + Math.random() * 20,
        cloBBB: base + 150 + Math.random() * 30,
        autoABS: base + 100 + Math.random() * 25,
        equipmentABS: base + 130 + Math.random() * 25,
        corpIG: 100 + Math.sin(i / 8) * 30,
        corpHY: base + 200 + Math.random() * 40,
      });
    }
    return data;
  }, []);

  const sectorData = [
    {
      sector: "CLO AAA",
      current: 245,
      historical: 220,
      benchmark: 120,
      spread: 125,
      zscore: 1.2,
      trend: "up",
    },
    {
      sector: "CLO Mezz (BBB)",
      current: 385,
      historical: 350,
      benchmark: 150,
      spread: 235,
      zscore: 0.8,
      trend: "down",
    },
    {
      sector: "Prime Auto ABS",
      current: 245,
      historical: 210,
      benchmark: 120,
      spread: 125,
      zscore: 1.5,
      trend: "up",
    },
    {
      sector: "Subprime Auto ABS",
      current: 425,
      historical: 400,
      benchmark: 250,
      spread: 175,
      zscore: 0.9,
      trend: "down",
    },
    {
      sector: "Equipment ABS",
      current: 320,
      historical: 300,
      benchmark: 130,
      spread: 190,
      zscore: 1.1,
      trend: "up",
    },
    {
      sector: "Consumer ABS",
      current: 380,
      historical: 360,
      benchmark: 200,
      spread: 180,
      zscore: 1.3,
      trend: "up",
    },
  ];

  const correlationData = [
    { x: "CLO AAA", y: "Auto ABS", correlation: 0.75 },
    { x: "CLO Mezz", y: "Corp BBB", correlation: 0.82 },
    { x: "Equipment", y: "IG Corps", correlation: 0.68 },
    { x: "Auto Prime", y: "IG Corps", correlation: 0.71 },
    { x: "Auto Sub", y: "HY Corps", correlation: 0.88 },
    { x: "Consumer", y: "HY Corps", correlation: 0.79 },
  ];

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Spread Monitor</h1>
          <p className="text-muted-foreground">Track relative value across structured credit sectors</p>
        </div>

        {/* Spread Trends */}
        <div className="bg-card rounded-xl p-6 border border-border mb-8">
          <h3 className="text-lg font-bold text-foreground mb-4">Historical Spread Trends (24 Months)</h3>
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={spreadData}>
              <defs>
                <linearGradient id="colorCloAAA" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0d5a9b" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#0d5a9b" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorAutoABS" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: "Spread (bps)", angle: -90, position: "insideLeft" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                formatter={(value: any) => `${(value || 0).toFixed(0)} bps`}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="cloAAA"
                stroke="#0d5a9b"
                fillOpacity={1}
                fill="url(#colorCloAAA)"
                name="CLO AAA"
              />
              <Area
                type="monotone"
                dataKey="cloBBB"
                stroke="#058fc7"
                fillOpacity={0.3}
                name="CLO Mezz (BBB)"
              />
              <Area
                type="monotone"
                dataKey="autoABS"
                stroke="#10b981"
                fillOpacity={1}
                fill="url(#colorAutoABS)"
                name="Auto ABS"
              />
              <Area type="monotone" dataKey="corpIG" stroke="#f59e0b" fillOpacity={0.3} name="Corp IG" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Snapshot */}
        <div className="mb-8">
          <h3 className="text-lg font-bold text-foreground mb-4">Sector Snapshot</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sectorData.map((sector, idx) => (
              <div key={idx} className="bg-card rounded-lg p-4 border border-border hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-bold text-foreground">{sector.sector}</p>
                    <p className="text-sm text-muted-foreground">vs Corp Benchmark</p>
                  </div>
                  {sector.trend === "up" ? (
                    <TrendingUp className="w-5 h-5 text-red-500" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-green-500" />
                  )}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">Current Spread</span>
                    <span className="font-bold text-foreground">{sector.current} bps</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">vs Historical</span>
                    <span className={`font-semibold ${sector.current > sector.historical ? "text-red-600" : "text-green-600"}`}>
                      {sector.current > sector.historical ? "+" : "-"}
                      {Math.abs(sector.current - sector.historical)} bps
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">Z-Score</span>
                    <span className={`font-semibold px-2 py-1 rounded text-xs ${
                      Math.abs(sector.zscore) > 1.5
                        ? "bg-red-100 text-red-700"
                        : Math.abs(sector.zscore) > 1
                        ? "bg-amber-100 text-amber-700"
                        : "bg-green-100 text-green-700"
                    }`}>
                      {sector.zscore.toFixed(1)}σ
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Spread Differential Analysis */}
        <div className="bg-card rounded-xl p-6 border border-border mb-8">
          <h3 className="text-lg font-bold text-foreground mb-4">Relative Value: Structured vs. Corporate</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                { sector: "CLO AAA", structured: 245, corporate: 120, differential: 125 },
                { sector: "CLO Mezz", structured: 385, corporate: 150, differential: 235 },
                { sector: "Auto Prime", structured: 245, corporate: 120, differential: 125 },
                { sector: "Equipment", structured: 320, corporate: 130, differential: 190 },
                { sector: "Consumer", structured: 380, corporate: 200, differential: 180 },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="sector" stroke="#6b7280" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                formatter={(value: any) => `${value || 0} bps`}
              />
              <Legend />
              <Bar dataKey="structured" fill="#0d5a9b" name="Structured Credit" />
              <Bar dataKey="corporate" fill="#f59e0b" name="Corporate Benchmark" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Key Metrics Table */}
        <div className="bg-card rounded-xl p-6 border border-border">
          <h3 className="text-lg font-bold text-foreground mb-4">Market Metrics Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left font-semibold text-foreground py-2 px-2">Sector</th>
                  <th className="text-right font-semibold text-foreground py-2 px-2">Current (bps)</th>
                  <th className="text-right font-semibold text-foreground py-2 px-2">Historical (bps)</th>
                  <th className="text-right font-semibold text-foreground py-2 px-2">Differential</th>
                  <th className="text-right font-semibold text-foreground py-2 px-2">Z-Score</th>
                  <th className="text-center font-semibold text-foreground py-2 px-2">Assessment</th>
                </tr>
              </thead>
              <tbody>
                {sectorData.map((sector, idx) => (
                  <tr key={idx} className="border-b border-border hover:bg-background transition-colors">
                    <td className="py-3 px-2 font-medium text-foreground">{sector.sector}</td>
                    <td className="py-3 px-2 text-right text-foreground">{sector.current}</td>
                    <td className="py-3 px-2 text-right text-muted-foreground">{sector.historical}</td>
                    <td className={`py-3 px-2 text-right font-semibold ${
                      sector.current > sector.historical ? "text-red-600" : "text-green-600"
                    }`}>
                      {sector.current > sector.historical ? "+" : ""}{sector.current - sector.historical}
                    </td>
                    <td className="py-3 px-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        Math.abs(sector.zscore) > 1.5
                          ? "bg-red-100 text-red-700"
                          : Math.abs(sector.zscore) > 1
                          ? "bg-amber-100 text-amber-700"
                          : "bg-green-100 text-green-700"
                      }`}>
                        {sector.zscore.toFixed(1)}σ
                      </span>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        sector.zscore > 1.5 ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
                      }`}>
                        {sector.zscore > 1.5 ? "Wide" : "Fair"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpreadMonitor;
