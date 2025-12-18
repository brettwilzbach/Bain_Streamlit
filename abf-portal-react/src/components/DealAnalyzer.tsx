"use client";

import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from "recharts";
import { ChevronDown } from "lucide-react";

const DealAnalyzer = () => {
  const [cpr, setCpr] = useState(20);
  const [cdr, setCdr] = useState(5);
  const [severity, setSeverity] = useState(60);
  const [selectedTranche, setSelectedTranche] = useState("classA");

  const [expandedSection, setExpandedSection] = useState<string | null>("overview");

  const dealStructure = {
    total: 500,
    classA: { size: 350, coupon: 2.5, oc: 1.2, rating: "AAA" },
    classB: { size: 100, coupon: 4.5, oc: 1.1, rating: "BBB" },
    classC: { size: 40, coupon: 8.0, oc: 1.0, rating: "BB" },
    equity: { size: 10 },
  };

  const generateCashFlows = useMemo(() => {
    const months = 60;
    const data = [];
    let balance = dealStructure.total;

    for (let i = 1; i <= months; i++) {
      const monthlyPrepay = (balance * (cpr / 100)) / 12;
      const monthlyDefault = (balance * (cdr / 100)) / 12;
      const recovery = monthlyDefault * (severity / 100);

      balance = Math.max(0, balance - monthlyPrepay - monthlyDefault + recovery);

      const classAPayment = Math.min(dealStructure.classA.size * (dealStructure.classA.coupon / 100 / 12), balance * 0.3);
      const classBPayment = Math.min(dealStructure.classB.size * (dealStructure.classB.coupon / 100 / 12), balance * 0.2);
      const classCPayment = Math.min(dealStructure.classC.size * (dealStructure.classC.coupon / 100 / 12), balance * 0.1);

      data.push({
        month: i,
        balance: parseFloat(balance.toFixed(1)),
        classA: parseFloat(classAPayment.toFixed(2)),
        classB: parseFloat(classBPayment.toFixed(2)),
        classC: parseFloat(classCPayment.toFixed(2)),
      });
    }

    return data;
  }, [cpr, cdr, severity]);

  const trancheReturns = useMemo(() => {
    return {
      classA: {
        irr: (2.5 + (cpr - 20) * 0.05).toFixed(2),
        moic: (1.0 + (cpr - 20) * 0.01).toFixed(2),
        wal: (8 - (cpr - 20) * 0.02).toFixed(1),
      },
      classB: {
        irr: (4.5 + (cpr - 20) * 0.1 - (cdr - 5) * 0.05).toFixed(2),
        moic: (1.05 + (cpr - 20) * 0.02 - (cdr - 5) * 0.01).toFixed(2),
        wal: (7 - (cpr - 20) * 0.015).toFixed(1),
      },
      classC: {
        irr: (8.0 + (cpr - 20) * 0.2 - (cdr - 5) * 0.15).toFixed(2),
        moic: (1.1 + (cpr - 20) * 0.05 - (cdr - 5) * 0.02).toFixed(2),
        wal: (5 - (cpr - 20) * 0.01).toFixed(1),
      },
    };
  }, [cpr, cdr]);

  const SectionHeader = ({ title, id }: { title: string; id: string }) => (
    <button
      onClick={() => setExpandedSection(expandedSection === id ? null : id)}
      className="w-full flex items-center justify-between p-4 bg-card border border-border rounded-lg hover:bg-background transition-colors mb-4"
    >
      <h3 className="text-lg font-bold text-foreground">{title}</h3>
      <ChevronDown
        size={20}
        className={`text-muted-foreground transition-transform ${expandedSection === id ? "rotate-180" : ""}`}
      />
    </button>
  );

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Deal Analyzer</h1>
          <p className="text-muted-foreground">Interactive ABS scenario modeling and analysis</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-card rounded-xl p-6 border border-border">
            <label className="block text-sm font-semibold text-foreground mb-3">
              Prepayment Speed (CPR): {cpr}%
            </label>
            <input
              type="range"
              min="0"
              max="60"
              value={cpr}
              onChange={(e) => setCpr(Number(e.target.value))}
              className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-muted-foreground mt-2">
              0% = No prepayment | 60% = Rapid payoff
            </p>
          </div>

          <div className="bg-card rounded-xl p-6 border border-border">
            <label className="block text-sm font-semibold text-foreground mb-3">
              Cumulative Default Rate (CDR): {cdr}%
            </label>
            <input
              type="range"
              min="0"
              max="30"
              value={cdr}
              onChange={(e) => setCdr(Number(e.target.value))}
              className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-muted-foreground mt-2">
              0% = No defaults | 30% = Severe stress
            </p>
          </div>

          <div className="bg-card rounded-xl p-6 border border-border">
            <label className="block text-sm font-semibold text-foreground mb-3">
              Recovery Severity: {severity}%
            </label>
            <input
              type="range"
              min="20"
              max="100"
              value={severity}
              onChange={(e) => setSeverity(Number(e.target.value))}
              className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-muted-foreground mt-2">
              20% = Severe loss | 100% = Full recovery
            </p>
          </div>
        </div>

        {/* Overview */}
        <SectionHeader title="Deal Overview" id="overview" />
        {expandedSection === "overview" && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {Object.entries(dealStructure).map(([key, value]: [string, any]) => (
              <div key={key} className="bg-card rounded-lg p-4 border border-border">
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-1 tracking-wide">
                  {key === "classA" ? "Class A" : key === "classB" ? "Class B" : key === "classC" ? "Class C" : "Equity"}
                </p>
                <p className="text-2xl font-bold text-foreground">${value.size}M</p>
                {value.coupon && <p className="text-xs text-muted-foreground mt-1">{value.coupon}% Coupon</p>}
                {value.rating && <p className="text-xs text-muted-foreground">{value.rating} Rating</p>}
              </div>
            ))}
          </div>
        )}

        {/* Tranche Returns */}
        <SectionHeader title="Tranche Returns Analysis" id="returns" />
        {expandedSection === "returns" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {["classA", "classB", "classC"].map((tranche) => (
              <div
                key={tranche}
                className={`bg-card rounded-xl p-6 border-2 cursor-pointer transition-all ${
                  selectedTranche === tranche
                    ? "border-primary shadow-lg"
                    : "border-border hover:border-muted"
                }`}
                onClick={() => setSelectedTranche(tranche)}
              >
                <h4 className="font-bold text-foreground mb-4">
                  {tranche === "classA" ? "Class A" : tranche === "classB" ? "Class B" : "Class C"}
                </h4>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Expected IRR</p>
                    <p className="text-2xl font-bold text-primary">
                      {trancheReturns[tranche as keyof typeof trancheReturns].irr}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">MOIC</p>
                    <p className="text-xl font-bold text-foreground">
                      {trancheReturns[tranche as keyof typeof trancheReturns].moic}x
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Weighted Avg Life</p>
                    <p className="text-lg font-bold text-foreground">
                      {trancheReturns[tranche as keyof typeof trancheReturns].wal} yrs
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Cash Flow Chart */}
        <SectionHeader title="Collateral Balance Projection" id="cashflow" />
        {expandedSection === "cashflow" && (
          <div className="bg-card rounded-xl p-6 border border-border mb-8">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={generateCashFlows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                  formatter={(value: any) => `$${(value || 0).toFixed(1)}M`}
                />
                <Legend />
                <Line type="monotone" dataKey="balance" stroke="#0d5a9b" strokeWidth={2} name="Pool Balance" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Monthly Payments Chart */}
        <SectionHeader title="Monthly Tranche Payments" id="payments" />
        {expandedSection === "payments" && (
          <div className="bg-card rounded-xl p-6 border border-border">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={generateCashFlows.slice(0, 12)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb" }}
                  formatter={(value: any) => `$${(value || 0).toFixed(2)}M`}
                />
                <Legend />
                <Bar dataKey="classA" fill="#0d5a9b" name="Class A" />
                <Bar dataKey="classB" fill="#058fc7" name="Class B" />
                <Bar dataKey="classC" fill="#10b981" name="Class C" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default DealAnalyzer;
