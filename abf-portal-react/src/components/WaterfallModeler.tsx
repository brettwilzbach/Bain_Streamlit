"use client";

import { useState } from "react";
import { ChevronDown, Plus } from "lucide-react";

const WaterfallModeler = () => {
  const [dealType, setDealType] = useState("auto");
  const [collateralBalance, setCollateralBalance] = useState(500);
  const [defaultRate, setDefaultRate] = useState(5);
  const [month, setMonth] = useState(1);

  const dealTemplates = {
    auto: {
      name: "Auto ABS",
      collateral: 500,
      tranches: [
        { name: "Class A", size: 350, coupon: 2.5, rating: "AAA" },
        { name: "Class B", size: 100, coupon: 4.5, rating: "BBB" },
        { name: "Class C", size: 40, coupon: 8.0, rating: "BB" },
      ],
      triggers: {
        oc: 1.15,
        ic: 1.25,
        cnl: 0.15,
      },
    },
    equipment: {
      name: "Equipment ABS",
      collateral: 300,
      tranches: [
        { name: "Class A", size: 210, coupon: 2.8, rating: "AAA" },
        { name: "Class B", size: 60, coupon: 5.0, rating: "A" },
        { name: "Class C", size: 24, coupon: 8.5, rating: "BB" },
      ],
      triggers: {
        oc: 1.2,
        ic: 1.3,
        cnl: 0.2,
      },
    },
    clo: {
      name: "CLO",
      collateral: 750,
      tranches: [
        { name: "Class A-1", size: 450, coupon: 3.0, rating: "AAA" },
        { name: "Class A-2", size: 150, coupon: 3.5, rating: "AA" },
        { name: "Class B", size: 90, coupon: 6.0, rating: "BBB" },
        { name: "Class C", size: 45, coupon: 10.0, rating: "BB" },
      ],
      triggers: {
        oc: 1.25,
        ic: 1.5,
        cnl: 0.25,
      },
    },
  };

  const template = dealTemplates[dealType as keyof typeof dealTemplates];

  const calculateWaterfall = () => {
    const collections = (collateralBalance * (1 - defaultRate / 100)) + collateralBalance * defaultRate / 100 * 0.6;
    const seniors = template.tranches.filter((t) => t.rating.includes("AAA") || t.rating.includes("AA")).map((t) => t.size).reduce((a, b) => a + b, 0);

    return {
      collections,
      defaultLoss: collateralBalance * defaultRate / 100 * 0.4,
      availableForPayment: collections,
    };
  };

  const waterfall = calculateWaterfall();

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Waterfall Modeler</h1>
          <p className="text-muted-foreground">Model deal structures and cash flow priorities</p>
        </div>

        {/* Template Selection */}
        <div className="bg-card rounded-xl p-6 border border-border mb-8">
          <h3 className="text-lg font-bold text-foreground mb-4">Deal Template</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(dealTemplates).map(([key, value]) => (
              <button
                key={key}
                onClick={() => setDealType(key)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  dealType === key
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted"
                }`}
              >
                <p className="font-semibold text-foreground text-left">{value.name}</p>
                <p className="text-sm text-muted-foreground text-left mt-1">${value.collateral}M Collateral</p>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Input Controls */}
          <div className="bg-card rounded-xl p-6 border border-border">
            <label className="block text-sm font-semibold text-foreground mb-3">
              Collateral Balance: ${collateralBalance}M
            </label>
            <input
              type="range"
              min="100"
              max="1000"
              step="50"
              value={collateralBalance}
              onChange={(e) => setCollateralBalance(Number(e.target.value))}
              className="w-full h-2 bg-border rounded-lg cursor-pointer"
            />

            <label className="block text-sm font-semibold text-foreground mb-3 mt-6">
              Default Rate: {defaultRate}%
            </label>
            <input
              type="range"
              min="0"
              max="30"
              value={defaultRate}
              onChange={(e) => setDefaultRate(Number(e.target.value))}
              className="w-full h-2 bg-border rounded-lg cursor-pointer"
            />

            <label className="block text-sm font-semibold text-foreground mb-3 mt-6">
              Month: {month}
            </label>
            <input
              type="range"
              min="1"
              max="60"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="w-full h-2 bg-border rounded-lg cursor-pointer"
            />
          </div>

          {/* Waterfall Summary */}
          <div className="bg-card rounded-xl p-6 border border-border">
            <h4 className="font-bold text-foreground mb-4">Waterfall Summary</h4>
            <div className="space-y-3">
              <div className="p-3 bg-background rounded-lg border border-border">
                <p className="text-xs text-muted-foreground mb-1">Collections</p>
                <p className="text-xl font-bold text-emerald-600">
                  ${waterfall.collections.toFixed(1)}M
                </p>
              </div>
              <div className="p-3 bg-background rounded-lg border border-border">
                <p className="text-xs text-muted-foreground mb-1">Default Loss</p>
                <p className="text-xl font-bold text-red-600">
                  -${waterfall.defaultLoss.toFixed(1)}M
                </p>
              </div>
              <div className="p-3 bg-background rounded-lg border border-border">
                <p className="text-xs text-muted-foreground mb-1">Available for Payment</p>
                <p className="text-xl font-bold text-primary">
                  ${waterfall.availableForPayment.toFixed(1)}M
                </p>
              </div>
            </div>
          </div>

          {/* Triggers Status */}
          <div className="bg-card rounded-xl p-6 border border-border">
            <h4 className="font-bold text-foreground mb-4">Trigger Status</h4>
            <div className="space-y-3">
              <div className="p-3 bg-background rounded-lg border border-emerald-300 bg-emerald-50">
                <p className="text-xs font-semibold text-emerald-700">OC Test</p>
                <p className="text-sm text-emerald-700 mt-1">
                  {template.triggers.oc.toFixed(2)}x - PASSING
                </p>
              </div>
              <div className="p-3 bg-background rounded-lg border border-emerald-300 bg-emerald-50">
                <p className="text-xs font-semibold text-emerald-700">IC Test</p>
                <p className="text-sm text-emerald-700 mt-1">
                  {template.triggers.ic.toFixed(2)}x - PASSING
                </p>
              </div>
              <div className="p-3 bg-background rounded-lg border border-emerald-300 bg-emerald-50">
                <p className="text-xs font-semibold text-emerald-700">CNL Trigger</p>
                <p className="text-sm text-emerald-700 mt-1">
                  {(template.triggers.cnl * 100).toFixed(1)}% - OK
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Priority Waterfall */}
        <div className="bg-card rounded-xl p-8 border border-border">
          <h3 className="text-lg font-bold text-foreground mb-6">Payment Priority Waterfall</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="text-center min-w-[100px]">
                <p className="text-2xl font-bold text-foreground">${waterfall.collections.toFixed(1)}M</p>
                <p className="text-xs text-muted-foreground mt-1">Collections</p>
              </div>
              <div className="flex-1 h-1 bg-gradient-to-r from-primary to-secondary rounded-full" />
            </div>

            <div className="space-y-2 mt-8 ml-4">
              {[
                { label: "Senior Fees", amount: 1.5 },
                { label: "Class A Interest", amount: 4.4 },
                { label: "Class B Interest", amount: 3.75 },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-background rounded-lg border border-border"
                >
                  <span className="font-medium text-foreground">{item.label}</span>
                  <span className="font-bold text-primary">${item.amount.toFixed(2)}M</span>
                </div>
              ))}

              <div className="mt-6 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-blue-900">OC Test</span>
                  <span className="text-sm font-medium text-blue-700">
                    {template.triggers.oc.toFixed(2)}x ✓ PASSING
                  </span>
                </div>
                <p className="text-xs text-blue-700 mt-2">
                  {`If breached, remaining funds trapped in reserve and redirected to principal paydown`}
                </p>
              </div>

              {[
                { label: "Class C Interest", amount: 2.67 },
                { label: "Class A Principal", amount: 10.0 },
                { label: "Class B Principal", amount: 5.0 },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-background rounded-lg border border-border mt-2"
                >
                  <span className="font-medium text-foreground">{item.label}</span>
                  <span className="font-bold text-secondary">${item.amount.toFixed(2)}M</span>
                </div>
              ))}

              <div className="mt-4 p-3 bg-background rounded-lg border border-border flex items-center justify-between">
                <span className="font-medium text-foreground">Residual/Equity</span>
                <span className="font-bold text-accent">Remaining</span>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm font-semibold text-amber-900 mb-2">Key Concepts</p>
            <ul className="text-xs text-amber-800 space-y-1">
              <li>• Senior tranches receive interest and principal before junior tranches</li>
              <li>• OC/IC tests redirect cash if breached, extending senior WAL</li>
              <li>• CNL trigger may switch to sequential pay to protect remaining investors</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WaterfallModeler;
