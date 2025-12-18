"use client";

import { useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts";
import { ChevronDown, Download } from "lucide-react";

const MarketTracker = () => {
  const [collateralFilter, setCollateralFilter] = useState("all");
  const [ratingFilter, setRatingFilter] = useState("all");
  const [spreadRange, setSpreadRange] = useState([50, 500]);

  const deals = [
    {
      id: 1,
      name: "ACMAT 2025-4",
      issuer: "Ally Financial",
      collateral: "Auto",
      size: 2500,
      pricingDate: "2025-01-15",
      ratings: ["AAA", "AA", "BBB", "BB"],
      spreads: [215, 280, 385, 520],
      bookrunner: "Goldman Sachs",
      format: "144A",
    },
    {
      id: 2,
      name: "EXETER 2025-1",
      issuer: "Exeter Finance",
      collateral: "Auto",
      size: 1800,
      pricingDate: "2025-01-14",
      ratings: ["AAA", "AA", "BBB"],
      spreads: [220, 290, 395],
      bookrunner: "Morgan Stanley",
      format: "144A",
    },
    {
      id: 3,
      name: "CLOS 2025-1",
      issuer: "BDC CLO Manager",
      collateral: "CLO",
      size: 3200,
      pricingDate: "2025-01-10",
      ratings: ["AAA", "AA", "BBB", "BB"],
      spreads: [245, 310, 450, 650],
      bookrunner: "Barclays",
      format: "Reg S",
    },
    {
      id: 4,
      name: "EQUIP 2025-2",
      issuer: "Wells Fargo",
      collateral: "Equipment",
      size: 950,
      pricingDate: "2025-01-08",
      ratings: ["AAA", "BBB"],
      spreads: [200, 320],
      bookrunner: "JPMorgan",
      format: "144A",
    },
    {
      id: 5,
      name: "CSAIL 2025-1",
      issuer: "Capital One",
      collateral: "Consumer",
      size: 2100,
      pricingDate: "2025-01-06",
      ratings: ["AAA", "AA", "BBB", "B"],
      spreads: [235, 300, 420, 580],
      bookrunner: "Bank of America",
      format: "144A",
    },
    {
      id: 6,
      name: "EXOTICA 2025-1",
      issuer: "Specialty Finance",
      collateral: "Esoteric",
      size: 450,
      pricingDate: "2025-01-02",
      ratings: ["AAA", "BBB"],
      spreads: [280, 480],
      bookrunner: "Citi",
      format: "Private",
    },
  ];

  const collateralTypes = ["Auto", "CLO", "Equipment", "Consumer", "Esoteric"];

  const filteredDeals = useMemo(() => {
    return deals.filter((deal) => {
      const collateralMatch = collateralFilter === "all" || deal.collateral === collateralFilter;
      const ratingMatch = ratingFilter === "all" || deal.ratings.includes(ratingFilter);
      const spreadMatch = deal.spreads.some((s) => s >= spreadRange[0] && s <= spreadRange[1]);
      return collateralMatch && ratingMatch && spreadMatch;
    });
  }, [collateralFilter, ratingFilter, spreadRange]);

  const issuanceByMonth = [
    { month: "Dec", volume: 8500, count: 8 },
    { month: "Jan", volume: 12200, count: 6 },
  ];

  const collateralDistribution = [
    { sector: "Auto", amount: 4300 },
    { sector: "CLO", amount: 3200 },
    { sector: "Equipment", amount: 950 },
    { sector: "Consumer", amount: 2100 },
    { sector: "Esoteric", amount: 450 },
  ];

  const spreadByRating = [
    { rating: "AAA", avg: 223 },
    { rating: "AA", avg: 295 },
    { rating: "BBB", avg: 413 },
    { rating: "BB", avg: 585 },
    { rating: "B", avg: 580 },
  ];

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Market Tracker</h1>
          <p className="text-muted-foreground">Monitor new ABS/CLO issuance and market activity</p>
        </div>

        {/* Analytics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-card rounded-xl p-4 border border-border">
            <p className="text-sm text-muted-foreground mb-1">2025 YTD Issuance</p>
            <p className="text-2xl font-bold text-primary">$12.2B</p>
            <p className="text-xs text-green-600 mt-1">+43.5% vs Dec</p>
          </div>
          <div className="bg-card rounded-xl p-4 border border-border">
            <p className="text-sm text-muted-foreground mb-1">Deals This Month</p>
            <p className="text-2xl font-bold text-primary">6</p>
            <p className="text-xs text-muted-foreground mt-1">Avg size: $2.0B</p>
          </div>
          <div className="bg-card rounded-xl p-4 border border-border">
            <p className="text-sm text-muted-foreground mb-1">Avg AAA Spread</p>
            <p className="text-2xl font-bold text-primary">223 bps</p>
            <p className="text-xs text-red-600 mt-1">+12 bps vs week ago</p>
          </div>
          <div className="bg-card rounded-xl p-4 border border-border">
            <p className="text-sm text-muted-foreground mb-1">Top Collateral</p>
            <p className="text-2xl font-bold text-primary">Auto</p>
            <p className="text-xs text-muted-foreground mt-1">35% of volume</p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-card rounded-xl p-6 border border-border">
            <h3 className="text-lg font-bold text-foreground mb-4">Issuance Volume by Month</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={issuanceByMonth}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" />
                <YAxis stroke="#6b7280" label={{ value: "$M", angle: -90, position: "insideLeft" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                  formatter={(value: any) => `$${value || 0}M`}
                />
                <Legend />
                <Bar dataKey="volume" fill="#0d5a9b" name="Volume" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-card rounded-xl p-6 border border-border">
            <h3 className="text-lg font-bold text-foreground mb-4">Collateral Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={collateralDistribution} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" stroke="#6b7280" />
                <YAxis dataKey="sector" type="category" stroke="#6b7280" width={80} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                  formatter={(value: any) => `$${value || 0}M`}
                />
                <Bar dataKey="amount" fill="#058fc7" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-card rounded-xl p-6 border border-border mb-8">
          <h3 className="text-lg font-bold text-foreground mb-4">Average Spread by Rating</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={spreadByRating}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="rating" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: "bps", angle: -90, position: "insideLeft" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                formatter={(value: any) => `${value || 0} bps`}
              />
              <Line type="monotone" dataKey="avg" stroke="#0d5a9b" strokeWidth={2} name="Avg Spread" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Filters */}
        <div className="bg-card rounded-xl p-6 border border-border mb-8">
          <h3 className="text-lg font-bold text-foreground mb-4">Filter Deals</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">Collateral Type</label>
              <select
                value={collateralFilter}
                onChange={(e) => setCollateralFilter(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">All Types</option>
                {collateralTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">Rating</label>
              <select
                value={ratingFilter}
                onChange={(e) => setRatingFilter(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">All Ratings</option>
                <option value="AAA">AAA</option>
                <option value="AA">AA</option>
                <option value="BBB">BBB</option>
                <option value="BB">BB</option>
                <option value="B">B</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">
                Spread Range: {spreadRange[0]} - {spreadRange[1]} bps
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="0"
                  max="500"
                  value={spreadRange[0]}
                  onChange={(e) => setSpreadRange([Number(e.target.value), spreadRange[1]])}
                  className="w-1/2 px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                />
                <input
                  type="number"
                  min="0"
                  max="500"
                  value={spreadRange[1]}
                  onChange={(e) => setSpreadRange([spreadRange[0], Number(e.target.value)])}
                  className="w-1/2 px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Deals Table */}
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-foreground">
                New Issuance Deals ({filteredDeals.length})
              </h3>
              <button className="flex items-center gap-2 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
                <Download size={16} />
                Export
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-background border-b border-border">
                  <th className="text-left font-semibold text-foreground py-3 px-4">Deal Name</th>
                  <th className="text-left font-semibold text-foreground py-3 px-4">Issuer</th>
                  <th className="text-left font-semibold text-foreground py-3 px-4">Collateral</th>
                  <th className="text-right font-semibold text-foreground py-3 px-4">Size ($M)</th>
                  <th className="text-center font-semibold text-foreground py-3 px-4">Pricing Date</th>
                  <th className="text-center font-semibold text-foreground py-3 px-4">AAA Spread</th>
                  <th className="text-center font-semibold text-foreground py-3 px-4">BBB Spread</th>
                  <th className="text-left font-semibold text-foreground py-3 px-4">Bookrunner</th>
                </tr>
              </thead>
              <tbody>
                {filteredDeals.map((deal) => (
                  <tr key={deal.id} className="border-b border-border hover:bg-background transition-colors">
                    <td className="py-3 px-4 font-medium text-foreground">{deal.name}</td>
                    <td className="py-3 px-4 text-foreground">{deal.issuer}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                        {deal.collateral}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-foreground">${deal.size}</td>
                    <td className="py-3 px-4 text-center text-muted-foreground text-sm">{deal.pricingDate}</td>
                    <td className="py-3 px-4 text-center font-bold text-primary">{deal.spreads[0]} bps</td>
                    <td className="py-3 px-4 text-center font-bold text-primary">{deal.spreads[2]} bps</td>
                    <td className="py-3 px-4 text-sm text-muted-foreground">{deal.bookrunner}</td>
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

export default MarketTracker;
