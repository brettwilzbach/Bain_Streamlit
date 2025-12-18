"use client";

import { useState } from "react";
import { BarChart3, TrendingUp, Zap, BookOpen, Menu, X } from "lucide-react";
import Dashboard from "@/components/Dashboard";
import DealAnalyzer from "@/components/DealAnalyzer";
import WaterfallModeler from "@/components/WaterfallModeler";
import SpreadMonitor from "@/components/SpreadMonitor";
import MarketTracker from "@/components/MarketTracker";

export default function Home() {
  const [activeModule, setActiveModule] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const modules = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3, color: "text-blue-600" },
    { id: "analyzer", label: "Deal Analyzer", icon: BookOpen, color: "text-blue-600" },
    { id: "waterfall", label: "Waterfall Modeler", icon: Zap, color: "text-cyan-600" },
    { id: "spread", label: "Spread Monitor", icon: TrendingUp, color: "text-emerald-600" },
    { id: "market", label: "Market Tracker", icon: BarChart3, color: "text-amber-600" },
  ];

  const renderModule = () => {
    switch (activeModule) {
      case "analyzer":
        return <DealAnalyzer />;
      case "waterfall":
        return <WaterfallModeler />;
      case "spread":
        return <SpreadMonitor />;
      case "market":
        return <MarketTracker />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-20"
        } transition-all duration-300 ease-in-out bg-sidebar border-r border-sidebar-border flex flex-col`}
      >
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <h1 className="font-bold text-sm text-sidebar-foreground whitespace-nowrap">ABF Portal</h1>
              </div>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 hover:bg-sidebar-accent/20 rounded-lg transition-colors text-sidebar-foreground"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {modules.map((module) => {
            const Icon = module.icon;
            const isActive = activeModule === module.id;
            return (
              <button
                key={module.id}
                onClick={() => setActiveModule(module.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                  isActive
                    ? "bg-sidebar-primary text-white shadow-lg shadow-sidebar-primary/30"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/20"
                } ${!sidebarOpen && "justify-center"}`}
              >
                <Icon size={20} className={isActive ? "text-white" : module.color} />
                {sidebarOpen && (
                  <span className="text-sm font-medium whitespace-nowrap">{module.label}</span>
                )}
              </button>
            );
          })}
        </nav>

        {sidebarOpen && (
          <div className="p-4 border-t border-sidebar-border text-xs text-sidebar-foreground/60">
            <p>Built for Bain Capital Credit</p>
            <p className="mt-1">ABF/Structured Credit</p>
          </div>
        )}
      </aside>

      <main className="flex-1 overflow-auto">
        {renderModule()}
      </main>
    </div>
  );
}
