"use client";

import { BarChart3, TrendingUp, BookOpen, Zap, DollarSign, Activity } from "lucide-react";

const Dashboard = () => {
  const metrics = [
    { label: "Total ABF Market", value: "$20T+", icon: DollarSign, color: "from-blue-600 to-blue-400" },
    { label: "Private ABF", value: "~$6T", icon: Activity, color: "from-cyan-600 to-cyan-400" },
    { label: "2024 Private ABS", value: "$130B", icon: TrendingUp, color: "from-emerald-600 to-emerald-400" },
    { label: "Projected (5yr)", value: "$200B", icon: BarChart3, color: "from-amber-600 to-amber-400" },
  ];

  const modules = [
    {
      id: 1,
      title: "Deal Analyzer",
      icon: BookOpen,
      color: "blue",
      description: "Educational ABS Explorer with interactive scenario sliders. See how CPR/CDR/severity affect returns with OC trigger visualization.",
      features: ["Interactive Scenarios", "Bond Returns", "Trigger Visualization"],
    },
    {
      id: 2,
      title: "Waterfall Modeler",
      icon: Zap,
      color: "cyan",
      description: "Advanced deal modeling with pre-built templates. Create custom deals with OC, IC, CNL triggers and break-even analysis.",
      features: ["Pre-built Templates", "Custom Inputs", "Break-even Analysis"],
    },
    {
      id: 3,
      title: "Spread Monitor",
      icon: TrendingUp,
      color: "emerald",
      description: "Track relative value across structured credit. Monitor historical trends and Z-scores across multiple sectors.",
      features: ["Market Data", "Benchmarks", "Historical Trends"],
    },
    {
      id: 4,
      title: "Market Tracker",
      icon: BarChart3,
      color: "amber",
      description: "Monitor new issuance across structured credit. Filter deals and access comprehensive analytics and export capabilities.",
      features: ["Deal Database", "Advanced Filters", "Export Tools"],
    },
  ];

  const colorClasses = {
    blue: "bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200 hover:border-blue-300",
    cyan: "bg-gradient-to-br from-cyan-50 to-cyan-100/50 border-cyan-200 hover:border-cyan-300",
    emerald: "bg-gradient-to-br from-emerald-50 to-emerald-100/50 border-emerald-200 hover:border-emerald-300",
    amber: "bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200 hover:border-amber-300",
  };

  const iconColorClasses = {
    blue: "text-blue-600",
    cyan: "text-cyan-600",
    emerald: "text-emerald-600",
    amber: "text-amber-600",
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="px-8 py-12">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-3">
            ABF/Structured Credit Analytics Portal
          </h1>
          <p className="text-lg text-muted-foreground">
            Interactive tools for analyzing Asset-Based Finance and Structured Credit products
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {metrics.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <div
                key={index}
                className="bg-card rounded-xl p-6 border border-border shadow-sm hover:shadow-md transition-shadow"
              >
                <div className={`w-12 h-12 bg-gradient-to-br ${metric.color} rounded-lg flex items-center justify-center mb-4`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <p className="text-sm text-muted-foreground mb-1">{metric.label}</p>
                <p className="text-2xl font-bold text-foreground">{metric.value}</p>
              </div>
            );
          })}
        </div>

        <div className="mb-12">
          <h2 className="text-2xl font-bold text-foreground mb-6">Portal Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {modules.map((module) => {
              const Icon = module.icon;
              const colorClass = colorClasses[module.color as keyof typeof colorClasses];
              const iconColor = iconColorClasses[module.color as keyof typeof iconColorClasses];
              return (
                <div
                  key={module.id}
                  className={`${colorClass} rounded-xl p-6 border transition-all duration-200 hover:shadow-lg cursor-pointer transform hover:scale-105`}
                >
                  <div className="flex items-start gap-4">
                    <Icon className={`w-8 h-8 ${iconColor} flex-shrink-0 mt-1`} />
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-foreground mb-2">{module.title}</h3>
                      <p className="text-sm text-foreground/70 mb-4">{module.description}</p>
                      <div className="flex flex-wrap gap-2">
                        {module.features.map((feature, idx) => (
                          <span
                            key={idx}
                            className={`text-xs px-2.5 py-1 rounded-full ${
                              module.color === "blue"
                                ? "bg-blue-200 text-blue-700"
                                : module.color === "cyan"
                                ? "bg-cyan-200 text-cyan-700"
                                : module.color === "emerald"
                                ? "bg-emerald-200 text-emerald-700"
                                : "bg-amber-200 text-amber-700"
                            }`}
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          <div className="bg-card rounded-xl p-6 border border-border">
            <h3 className="text-xl font-bold text-foreground mb-4">ABF Collateral Universe</h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-foreground mb-2 text-sm">Consumer Assets</h4>
                <p className="text-sm text-muted-foreground">
                  Prime/Subprime Auto Loans, Credit Card Receivables, Personal Loans, BNPL, Student Loans
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-foreground mb-2 text-sm">Commercial Assets</h4>
                <p className="text-sm text-muted-foreground">
                  Equipment Leases, Fleet/Vehicle Leases, Small Business Loans, Franchise Loans
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-foreground mb-2 text-sm">Hard Assets</h4>
                <p className="text-sm text-muted-foreground">
                  Aircraft Leases, Railcar, Shipping, Solar/PACE, Data Centers
                </p>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-xl p-6 border border-border">
            <h3 className="text-xl font-bold text-foreground mb-4">Key Concepts</h3>
            <div className="space-y-3">
              <div className="p-3 bg-background rounded-lg border border-border">
                <h4 className="font-semibold text-foreground text-sm mb-1">OC Test</h4>
                <p className="text-xs text-muted-foreground">
                  Collateral Value / Outstanding Notes. Ensures sufficient collateral to cover debt.
                </p>
              </div>
              <div className="p-3 bg-background rounded-lg border border-border">
                <h4 className="font-semibold text-foreground text-sm mb-1">IC Test</h4>
                <p className="text-xs text-muted-foreground">
                  Interest Income / Interest Expense. Ensures interest income covers interest payments.
                </p>
              </div>
              <div className="p-3 bg-background rounded-lg border border-border">
                <h4 className="font-semibold text-foreground text-sm mb-1">Sequential vs. Pro-Rata</h4>
                <p className="text-xs text-muted-foreground">
                  Sequential pays seniors first. Pro-rata pays all proportionally. Typically switches on trigger.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
