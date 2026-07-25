import React, { useState, useEffect, useRef } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from "recharts";
import {
  Play,
  Pause,
  RotateCcw,
  Zap,
  Activity,
  User,
  Thermometer,
  Sliders,
  Cpu,
  RefreshCw,
  AlertOctagon,
  Leaf,
  Layers,
  Sparkles,
  Database,
  Building,
  BarChart3,
  Settings,
  MoreVertical,
  Clock,
  TrendingDown,
  Users,
  Sun,
  Moon
} from "lucide-react";

const API_BASE = "http://localhost:8000/api";

const DEFAULT_HISTORICAL_DATA = Array.from({ length: 24 }, (_, idx) => {
  const hr = idx;
  const outTemp = 22.0 + 10.0 * Math.sin((hr - 6) / 12 * Math.PI);
  return {
    hour: hr,
    outdoor_temp: outTemp,
    temperatures: {
      "Zone 1: Open Office": 21.5 + Math.sin(hr / 4),
      "Zone 2: Meeting Room": 22.0 + 1.2 * Math.sin(hr / 5),
      "Zone 3: Executive Suite": 21.8 + 0.8 * Math.cos(hr / 3)
    },
    cooling_setpoints: {
      "Zone 1: Open Office": 22.5,
      "Zone 2: Meeting Room": 23.0,
      "Zone 3: Executive Suite": 22.0
    },
    heating_setpoints: {
      "Zone 1: Open Office": 20.0,
      "Zone 2: Meeting Room": 19.5,
      "Zone 3: Executive Suite": 20.0
    },
    energy_kwh: 1.2 + 0.8 * Math.sin(hr / 6),
    carbon_intensity: 120 + 200 * Math.max(0, Math.sin((hr - 10) / 4)),
    carbon_kg: 0.15 + 0.1 * Math.sin(hr / 6),
    comfort_penalty: 0.05 + 0.05 * Math.cos(hr / 4)
  };
});

export default function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState("Dashboard");

  const [buildingState, setBuildingState] = useState({
    step: 0,
    hour: 0.0,
    time_str: "00:00",
    outdoor_temp: 24.0,
    carbon_intensity: 210.0,
    zones: {},
    current_strategy: "None",
    last_explanation: "Waiting for simulation to begin."
  });

  const [metrics, setMetrics] = useState({
    baseline: { energy: 45.4, carbon: 9.8, comfort: 12.1, violations: 0 },
    sentient: { energy: 37.6, carbon: 8.0, comfort: 8.4, violations: 0 },
    savings: { energy: 17.3, carbon: 17.8, comfort: 30.5 }
  });

  const [safetyStatus, setSafetyStatus] = useState({
    violations_count: 0,
    last_gate_passed: true,
    last_violations: [],
    fallback_active: false
  });

  const [sentientHistory, setSentientHistory] = useState([]);
  const [baselineHistory, setBaselineHistory] = useState([]);
  const [selectedZone, setSelectedZone] = useState("Zone 1: Open Office");

  const [weights, setWeights] = useState({
    energy: 1.0,
    carbon: 0.5,
    comfort: 2.0
  });

  const [isPlaying, setIsPlaying] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);
  const [violationQueued, setViolationQueued] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const [zoneOverrides, setZoneOverrides] = useState({
    cooling: 22.0,
    heating: 20.0
  });

  const playIntervalRef = useRef(null);

  const fetchData = async () => {
    try {
      const stateRes = await fetch(`${API_BASE}/building/current`);
      const stateData = await stateRes.json();
      setBuildingState(stateData);

      const metricsRes = await fetch(`${API_BASE}/metrics`);
      const metricsData = await metricsRes.json();
      setMetrics(metricsData);

      const safetyRes = await fetch(`${API_BASE}/safety`);
      const safetyData = await safetyRes.json();
      setSafetyStatus(safetyData);

      const historyRes = await fetch(`${API_BASE}/simulation/data`);
      const historyData = await historyRes.json();
      setSentientHistory(historyData.sentient_history || []);
      setBaselineHistory(historyData.baseline_history || []);
      
      if (stateData.zones && Object.keys(stateData.zones).length > 0 && !stateData.zones[selectedZone]) {
        setSelectedZone(Object.keys(stateData.zones)[0]);
      }
      
      setErrorMsg("");
    } catch (err) {
      console.error(err);
      setErrorMsg("Failed to connect to backend API server. Verify FastAPI is running on localhost:8000.");
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (isPlaying) {
      playIntervalRef.current = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/simulation/step`, { method: "POST" });
          const stepRes = await res.json();
          if (stepRes.status === "finished" || buildingState.step >= 95) {
            setIsPlaying(false);
            clearInterval(playIntervalRef.current);
          }
          fetchData();
        } catch (err) {
          setIsPlaying(false);
          console.error(err);
        }
      }, 800);
    } else {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    }
    return () => {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    };
  }, [isPlaying, buildingState.step]);

  const handleStep = async () => {
    try {
      await fetch(`${API_BASE}/simulation/step`, { method: "POST" });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReset = async () => {
    setIsPlaying(false);
    try {
      await fetch(`${API_BASE}/simulation/reset`, { method: "POST" });
      setViolationQueued(false);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleInjectViolation = async () => {
    try {
      await fetch(`${API_BASE}/simulation/inject_violation`, { method: "POST" });
      setViolationQueued(true);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleWeightsSubmit = async () => {
    setIsRerunning(true);
    try {
      const res = await fetch(`${API_BASE}/weights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(weights)
      });
      const data = await res.json();
      setWeights(data.weights);
      fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsRerunning(false);
    }
  };

  const adjustWeight = (field, newVal) => {
    const val = parseFloat(newVal);
    const updated = { ...weights, [field]: val };
    setWeights(updated);
  };

  const hasHistory = sentientHistory.length > 0;
  const activeHistory = hasHistory ? sentientHistory : DEFAULT_HISTORICAL_DATA;
  const activeBaseline = baselineHistory.length > 0 ? baselineHistory : DEFAULT_HISTORICAL_DATA;

  const getSparklineData = (field, length = 12) => {
    return activeHistory.slice(-length).map((step) => ({
      value: field === "energy" ? step.energy_kwh : field === "carbon" ? (step.carbon_kg || (step.energy_kwh * 0.15)) : step.comfort_penalty
    }));
  };

  const getTempChartData = () => {
    return activeHistory.map((step, idx) => {
      const baseStep = activeBaseline[idx] || {};
      return {
        Hour: step.hour,
        Outdoor: step.outdoor_temp,
        [`${selectedZone} (AI)`]: step.temperatures[selectedZone] || 22.0,
        [`${selectedZone} (Base)`]: baseStep.temperatures ? baseStep.temperatures[selectedZone] : 22.0,
        "Cooling Setpoint": step.cooling_setpoints ? step.cooling_setpoints[selectedZone] : 24.0,
        "Heating Setpoint": step.heating_setpoints ? step.heating_setpoints[selectedZone] : 20.0
      };
    });
  };

  const getEnergyChartData = () => {
    return activeHistory.map((step, idx) => {
      const baseStep = activeBaseline[idx] || {};
      return {
        Hour: step.hour,
        "AI HVAC Energy (kWh)": step.energy_kwh,
        "Base HVAC Energy (kWh)": baseStep.energy_kwh || 0
      };
    });
  };

  const getOccupancyChartData = () => {
    return activeHistory.map((step) => {
      const keys = step.occupancies ? Object.keys(step.occupancies) : ["Zone 1: Open Office", "Zone 2: Meeting Room", "Zone 3: Executive Suite"];
      return {
        Hour: step.hour,
        "Zone 1: Open Office": step.occupancies ? step.occupancies[keys[0]] : 10,
        "Zone 2: Meeting Room": step.occupancies ? step.occupancies[keys[1]] : 5,
        "Zone 3: Executive Suite": step.occupancies ? step.occupancies[keys[2]] : 2
      };
    });
  };

  const currentDecision = activeHistory[activeHistory.length - 1] || null;

  // Adaptive classes based on active dark/light state
  const cardClass = darkMode ? "glass-card-dark p-6 rounded-2xl" : "glass-card-light p-6 rounded-2xl border border-slate-200 shadow-sm";
  const textClass = darkMode ? "text-white" : "text-slate-900";
  const subtextClass = darkMode ? "text-slate-400" : "text-slate-550";
  const borderClass = darkMode ? "border-white/5" : "border-slate-200";
  const bgClass = darkMode ? "bg-white/5" : "bg-slate-100";

  const renderDashboardView = () => (
    <div className="space-y-8">
      {/* 3. Top Row: High-Level KPIs */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card: HVAC Energy Cost */}
        <div className={`${cardClass} relative overflow-hidden flex flex-col justify-between hover:scale-[1.01] transition-all duration-300`}>
          <div className="absolute inset-x-0 bottom-0 h-10 pointer-events-none opacity-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={getSparklineData("energy")}>
                <Area type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={1.5} fill="#3B82F6" fillOpacity={0.2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between items-start mb-4">
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">HVAC Energy Cost</span>
              <p className="text-[10px] text-slate-500 font-sans">Active electrical input demand</p>
            </div>
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
              <Zap className="h-4.5 w-4.5" />
            </div>
          </div>
          <div className="flex items-baseline justify-between pt-2">
            <span className={`text-2xl font-black font-mono-tech tracking-tight ${textClass}`}>
              {metrics.sentient.energy} <span className="text-xs font-normal text-slate-400">kWh</span>
            </span>
            {metrics.savings.energy > 0 ? (
              <span className="text-xs font-bold text-emerald-500 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <TrendingDown size={11} />
                ↓ {metrics.savings.energy}%
              </span>
            ) : (
              <span className="text-[10px] text-slate-500 font-mono-tech">vs {metrics.baseline.energy}</span>
            )}
          </div>
        </div>

        {/* Card: Carbon Footprint */}
        <div className={`${cardClass} relative overflow-hidden flex flex-col justify-between hover:scale-[1.01] transition-all duration-300`}>
          <div className="absolute inset-x-0 bottom-0 h-10 pointer-events-none opacity-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={getSparklineData("carbon")}>
                <Area type="monotone" dataKey="value" stroke="#10B981" strokeWidth={1.5} fill="#10B981" fillOpacity={0.2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between items-start mb-4">
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Carbon Footprint</span>
              <p className="text-[10px] text-slate-500 font-sans">Active emissions footprint</p>
            </div>
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500">
              <Leaf className="h-4.5 w-4.5" />
            </div>
          </div>
          <div className="flex items-baseline justify-between pt-2">
            <span className={`text-2xl font-black font-mono-tech tracking-tight ${textClass}`}>
              {metrics.sentient.carbon} <span className="text-xs font-normal text-slate-400">kg CO₂</span>
            </span>
            {metrics.savings.carbon > 0 ? (
              <span className="text-xs font-bold text-emerald-500 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <TrendingDown size={11} />
                ↓ {metrics.savings.carbon}%
              </span>
            ) : (
              <span className="text-[10px] text-slate-500 font-mono-tech">vs {metrics.baseline.carbon}</span>
            )}
          </div>
        </div>

        {/* Card: Comfort Deviation */}
        <div className={`${cardClass} relative overflow-hidden flex flex-col justify-between hover:scale-[1.01] transition-all duration-300`}>
          <div className="absolute inset-x-0 bottom-0 h-10 pointer-events-none opacity-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={getSparklineData("comfort")}>
                <Area type="monotone" dataKey="value" stroke="#F59E0B" strokeWidth={1.5} fill="#F59E0B" fillOpacity={0.2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between items-start mb-4">
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Comfort Deviation</span>
              <p className="text-[10px] text-slate-500 font-sans">Boundary violation rate</p>
            </div>
            <div className="p-2 bg-amber-500/10 rounded-lg text-amber-500">
              <Thermometer className="h-4.5 w-4.5" />
            </div>
          </div>
          <div className="flex items-baseline justify-between pt-2">
            <span className={`text-2xl font-black font-mono-tech tracking-tight ${textClass}`}>
              {metrics.sentient.comfort}
            </span>
            {metrics.savings.comfort > 0 ? (
              <span className="text-xs font-bold text-emerald-500 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <TrendingDown size={11} />
                ↓ {metrics.savings.comfort}%
              </span>
            ) : (
              <span className="text-[10px] text-slate-500 font-mono-tech">vs {metrics.baseline.comfort}</span>
            )}
          </div>
        </div>
      </section>

      {/* 4. Middle Row: Strategy & Tuning (Split Layout) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Dynamic Objectives (Sliders Card) */}
        <div className={`${cardClass} flex flex-col justify-between relative`}>
          <div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400">
                  <Sliders size={16} />
                </div>
                <h3 className={`text-xs font-bold uppercase tracking-wider ${textClass}`}>Dynamic Strategy Tuning</h3>
              </div>
              <button className="text-slate-500 hover:text-slate-400 cursor-pointer"><MoreVertical size={16} /></button>
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-xs mb-2.5 font-bold uppercase tracking-wider text-slate-400">
                  <span>Energy Weight</span>
                  <span className="text-indigo-400 font-mono-tech font-bold">{weights.energy}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={weights.energy}
                  onChange={(e) => adjustWeight("energy", e.target.value)}
                  className="w-full appearance-none cursor-pointer premium-slider-violet"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-2.5 font-bold uppercase tracking-wider text-slate-400">
                  <span>Carbon Weight</span>
                  <span className="text-cyan-400 font-mono-tech font-bold">{weights.carbon}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={weights.carbon}
                  onChange={(e) => adjustWeight("carbon", e.target.value)}
                  className="w-full appearance-none cursor-pointer premium-slider-cyan"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-2.5 font-bold uppercase tracking-wider text-slate-400">
                  <span>Comfort Weight</span>
                  <span className="text-violet-400 font-mono-tech font-bold">{weights.comfort}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={weights.comfort}
                  onChange={(e) => adjustWeight("comfort", e.target.value)}
                  className="w-full appearance-none cursor-pointer premium-slider-violet"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleWeightsSubmit}
            disabled={isRerunning}
            className="w-full py-4 mt-8 bg-gradient-to-r from-indigo-600 to-violet-650 hover:from-indigo-500 hover:to-violet-550 text-white font-extrabold rounded-xl flex items-center justify-center gap-2 border border-indigo-500/25 text-xs uppercase tracking-wider cursor-pointer outline-none transition-all shadow-lg active:scale-[0.98]"
          >
            <RefreshCw size={14} className={isRerunning ? "animate-spin" : ""} />
            Compute Optimal Control Strategy
          </button>
        </div>

        {/* AI Strategy Sandbox Selection */}
        <div className={`${cardClass} flex flex-col justify-between relative`}>
          <div>
            <div className="flex justify-between items-center mb-5">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-cyan-500/10 rounded-lg text-cyan-400">
                  <Sparkles size={16} />
                </div>
                <h3 className={`text-xs font-bold uppercase tracking-wider ${textClass}`}>AI Sandbox Evaluations</h3>
              </div>
              <button className="text-slate-500 hover:text-slate-400 cursor-pointer"><MoreVertical size={16} /></button>
            </div>

            {hasHistory && currentDecision && currentDecision.candidate_strategies ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {currentDecision.candidate_strategies.map((strat) => {
                    const isSelected = strat.name === currentDecision.selected_strategy;
                    let themeBorder = isSelected 
                      ? "border-indigo-600 bg-indigo-500/10 shadow-[0_0_15px_rgba(99,102,241,0.15)]" 
                      : `${borderClass} bg-slate-900/30 hover:border-slate-700`;
                    
                    return (
                      <div key={strat.name} className={`p-4 rounded-xl border transition-all ${themeBorder}`}>
                        <div className="flex justify-between items-center mb-3">
                          <span className={`text-xs font-bold ${textClass} tracking-wide`}>{strat.name.split(" ")[0]}</span>
                          {isSelected && (
                            <span className="text-[9px] font-black text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 uppercase tracking-widest">
                              ACTIVE
                            </span>
                          )}
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Energy</span>
                            <span className={`font-mono-tech font-bold ${textClass}`}>{strat.energy_kwh.toFixed(1)} kWh</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Carbon</span>
                            <span className={`font-mono-tech font-bold ${textClass}`}>{strat.carbon_kg.toFixed(1)} kg</span>
                          </div>
                          <div className={`flex justify-between pt-2 border-t ${borderClass} font-bold`}>
                            <span className="text-slate-450">Score J</span>
                            <span className="font-mono-tech text-indigo-400">{strat.score.toFixed(3)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className={`p-4 ${bgClass} border ${borderClass} rounded-xl flex items-start gap-2.5`}>
                  <div className="p-1 bg-indigo-500/10 text-indigo-400 rounded-lg shrink-0 mt-0.5">
                    <Cpu size={12} />
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">Decision Reasoning</div>
                    <p className={`text-[11px] leading-relaxed font-sans ${textClass}`}>{currentDecision.explanation}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className={`h-[210px] border border-dashed ${borderClass} rounded-xl flex flex-col items-center justify-center space-y-3 relative overflow-hidden bg-slate-950/20`}>
                <div className="p-3 bg-indigo-500/5 text-indigo-400 rounded-full animate-pulse">
                  <Sparkles size={20} />
                </div>
                <div className="text-center space-y-1">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Awaiting Simulation Loop</span>
                  <p className="text-[10px] text-slate-500 max-w-[280px]">Run a simulation step to feed active variables into the AI Strategy Sandbox.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 5. Bottom Row: Zones & Logs (Split Layout) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Monitoring Grid */}
        <div className={`${cardClass}`}>
          <div className="flex justify-between items-center mb-5">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400">
                <Building size={16} />
              </div>
              <h3 className={`text-xs font-bold uppercase tracking-wider ${textClass}`}>Zone Monitoring Grid</h3>
            </div>
            <button className="text-slate-500 hover:text-white cursor-pointer"><MoreVertical size={16} /></button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {buildingState.zones && Object.keys(buildingState.zones).length > 0 ? (
              Object.keys(buildingState.zones).map((zoneName) => {
                const zone = buildingState.zones[zoneName];
                const isSelected = selectedZone === zoneName;
                const tempDeviates = Math.abs(zone.temperature - (zone.cooling_setpoint || 22.0)) > 2.0;
                
                return (
                  <div
                    key={zoneName}
                    onClick={() => setSelectedZone(zoneName)}
                    className={`p-4 rounded-xl cursor-pointer border transition-all ${
                      isSelected
                        ? "bg-indigo-500/10 border-indigo-500/80 shadow-md"
                        : "bg-slate-950/20 border-white/5 hover:bg-slate-900/40"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className={`text-xs font-bold ${textClass} truncate`}>{zoneName.split(":")[1]?.trim()}</span>
                    </div>
                    
                    <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-mono-tech mb-3">
                      <Users size={10} className="text-slate-500" />
                      <span>{zone.occupancy} OCCUPANTS</span>
                    </div>

                    <div className={`space-y-1.5 text-[11px] border-t ${borderClass} pt-2.5 font-mono-tech`}>
                      <div className="flex justify-between">
                        <span className="text-slate-550 font-sans">Current</span>
                        <span className={`font-bold ${tempDeviates ? "text-amber-500" : "text-cyan-500"}`}>{zone.temperature}°C</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-555 font-sans">Setpoint</span>
                        <span className={`font-bold ${darkMode ? "text-rose-400" : "text-rose-600"}`}>{zone.cooling_setpoint || zone.cooling_setpoint}°C</span>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              ["Zone 1: Open Office", "Zone 2: Meeting Room", "Zone 3: Executive Suite"].map((name) => {
                const isSelected = selectedZone === name;
                return (
                  <div
                    key={name}
                    onClick={() => setSelectedZone(name)}
                    className={`p-4 rounded-xl cursor-pointer border transition-all ${
                      isSelected
                        ? "bg-indigo-500/10 border-indigo-500/80 shadow-md"
                        : "bg-slate-950/20 border-white/5 hover:bg-slate-900/40"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className={`text-xs font-bold ${textClass} truncate`}>{name.split(":")[1].trim()}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-mono-tech mb-3">
                      <Users size={10} className="text-slate-500" />
                      <span>12 occupants</span>
                    </div>
                    <div className={`space-y-1.5 text-[11px] border-t ${borderClass} pt-2.5 font-mono-tech`}>
                      <div className="flex justify-between">
                        <span className="text-slate-555 font-sans">Current</span>
                        <span className="font-bold text-cyan-400">21.8°C</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-555 font-sans">Setpoint</span>
                        <span className="font-bold text-rose-450">22.5°C</span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Audit Timeline */}
        <div className={`${cardClass} flex flex-col justify-between`}>
          <div>
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400">
                  <Database size={16} />
                </div>
                <h3 className={`text-xs font-bold uppercase tracking-wider ${textClass}`}>Audit & Explainability Log</h3>
              </div>
              <button className="text-slate-500 hover:text-white cursor-pointer"><MoreVertical size={16} /></button>
            </div>

            <div className="h-44 overflow-y-auto pr-2 space-y-3 custom-scrollbar font-mono text-[11px]">
              {sentientHistory.length > 0 ? (
                [...sentientHistory].reverse().map((step) => {
                  const passStatus = !step.fallback_activated;
                  return (
                    <div key={step.step} className={`flex gap-3 border-b ${borderClass} pb-2.5 items-start`}>
                      <div className="w-16 shrink-0 text-slate-500 font-bold">[{step.time_str}]</div>
                      
                      <div className="flex-1 space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${
                            passStatus
                              ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-500 border border-rose-500/20 animate-pulse"
                          }`}>
                            {passStatus ? "PASS" : "FALLBACK"}
                          </span>
                          <span className={`text-[9px] ${subtextClass} font-extrabold uppercase font-sans tracking-wide`}>
                            {step.selected_strategy || step.ai_strategy}
                          </span>
                        </div>
                        <p className={`font-sans leading-normal ${textClass}`}>{step.explanation || step.ai_explanation}</p>
                      </div>
                    </div>
                  );
                })
              ) : (
                <>
                  <div className={`flex gap-3 border-b ${borderClass} pb-2.5 items-start`}>
                    <div className="w-16 shrink-0 text-slate-500 font-bold">[12:00]</div>
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-wider">PASS</span>
                        <span className={`text-[9px] ${subtextClass} font-extrabold uppercase font-sans`}>Carbon-Aware Mode</span>
                      </div>
                      <p className={`font-sans leading-normal ${textClass}`}>Grid carbon intensity spiked to 550g CO2/kWh. SentientBMS relaxed cooling setpoint to 23.5°C to shift HVAC loads.</p>
                    </div>
                  </div>
                  <div className={`flex gap-3 border-b ${borderClass} pb-2.5 items-start`}>
                    <div className="w-16 shrink-0 text-slate-500 font-bold">[10:00]</div>
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-wider">PASS</span>
                        <span className={`text-[9px] ${subtextClass} font-extrabold uppercase font-sans`}>Comfort-First Mode</span>
                      </div>
                      <p className={`font-sans leading-normal ${textClass}`}>Occupancy spike detected in Zone 2 Meeting Room (12 occupants). Lowered setpoint to 21.0°C to preserve ventilation stability.</p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );

  const renderZonesView = () => (
    <div className={`${cardClass} space-y-8 animate-fade-in`}>
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400">
            <Building size={22} />
          </div>
          <div>
            <h3 className={`text-sm font-black tracking-wide uppercase ${textClass}`}>Zone Management Console</h3>
            <p className="text-xs text-slate-500">Inspect and actuate zone setpoints dynamically</p>
          </div>
        </div>
        <button className="text-slate-500 hover:text-white cursor-pointer"><MoreVertical size={18} /></button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {(buildingState.zones && Object.keys(buildingState.zones).length > 0 ? Object.keys(buildingState.zones) : ["Zone 1: Open Office", "Zone 2: Meeting Room", "Zone 3: Executive Suite"]).map((zoneName) => {
          const zone = buildingState.zones[zoneName] || { temperature: 21.8, cooling_setpoint: 22.5, heating_setpoint: 20.0, occupancy: 12 };
          return (
            <div key={zoneName} className={`p-6 rounded-xl bg-slate-900/40 border ${borderClass} hover:border-indigo-500/30 transition-all duration-350 space-y-5`}>
              <h4 className={`font-bold border-b ${borderClass} pb-2.5 text-sm ${textClass}`}>{zoneName.split(":")[1]?.trim() || zoneName}</h4>
              
              <div className="space-y-3 text-xs font-mono-tech">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Current Temp:</span>
                  <span className="text-cyan-500 font-bold">{zone.temperature}°C</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Cooling Setpoint:</span>
                  <span className="text-rose-500 font-bold">{zone.cooling_setpoint}°C</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Heating Setpoint:</span>
                  <span className={`font-bold ${textClass}`}>{zone.heating_setpoint}°C</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Occupancy:</span>
                  <span className={textClass}>{zone.occupancy} Persons</span>
                </div>
              </div>

              {/* Setpoint Override Slider controls */}
              <div className={`space-y-3 pt-4 border-t ${borderClass}`}>
                <div className="text-[10px] font-bold text-slate-505 uppercase tracking-widest">Mock Setpoint Adjust</div>
                <div className="flex gap-2">
                  <button
                    onClick={() => alert(`${zoneName} Override Configured: Cooling set to ${zoneOverrides.cooling}°C`)}
                    className="flex-1 py-2 px-3 text-xs bg-indigo-650 hover:bg-indigo-600 text-white font-extrabold rounded-lg cursor-pointer transition-all"
                  >
                    Submit Actuation
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderAnalyticsView = () => (
    <div className={`${cardClass} space-y-8 animate-fade-in`}>
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400">
            <BarChart3 size={22} />
          </div>
          <div>
            <h3 className={`text-sm font-black tracking-wide uppercase ${textClass}`}>Historical Analytics Center</h3>
            <p className="text-xs text-slate-500">Comparative simulation profile overview</p>
          </div>
        </div>
        <button className="text-slate-500 hover:text-white cursor-pointer"><MoreVertical size={18} /></button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Temp Curve chart */}
        <div className={`bg-slate-900/40 border ${borderClass} p-6 rounded-xl relative overflow-hidden`}>
          <h4 className={`text-xs font-bold uppercase tracking-widest ${subtextClass} mb-4`}>Interactive Thermal Profiles</h4>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={getTempChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "rgba(255,255,255,0.03)" : "rgba(15, 23, 42, 0.05)"} />
                <XAxis dataKey="Hour" stroke="#475569" tickFormatter={(v) => `${Math.floor(v)}h`} className="text-[10px]" />
                <YAxis stroke="#475569" domain={[16, 38]} className="text-[10px]" />
                <Tooltip contentStyle={{ backgroundColor: darkMode ? "#0b0f1a" : "#ffffff", borderColor: darkMode ? "rgba(255,255,255,0.08)" : "#e2e8f0", color: darkMode ? "#e2e8f0" : "#0f172a" }} />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="Outdoor" stroke="#F59E0B" strokeWidth={1.5} dot={false} name="Outdoor Air" />
                <Line type="monotone" dataKey={`${selectedZone} (AI)`} stroke="#8B5CF6" strokeWidth={2.5} dot={false} name="AI Room Temp" />
                <Line type="monotone" dataKey="Cooling Setpoint" stroke="#F43F5E" strokeWidth={1.5} strokeDasharray="3 3" dot={false} name="Cooling Limit" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* HVAC energy curve */}
        <div className={`bg-slate-900/40 border ${borderClass} p-6 rounded-xl relative overflow-hidden`}>
          <h4 className={`text-xs font-bold uppercase tracking-widest ${subtextClass} mb-4`}>HVAC Electrical Profile (Comparative)</h4>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={getEnergyChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "rgba(255,255,255,0.03)" : "rgba(15, 23, 42, 0.05)"} />
                <XAxis dataKey="Hour" stroke="#475569" tickFormatter={(v) => `${Math.floor(v)}h`} className="text-[10px]" />
                <YAxis stroke="#475569" className="text-[10px]" />
                <Tooltip contentStyle={{ backgroundColor: darkMode ? "#0b0f1a" : "#ffffff", borderColor: darkMode ? "rgba(255,255,255,0.08)" : "#e2e8f0", color: darkMode ? "#e2e8f0" : "#0f172a" }} />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="AI HVAC Energy (kWh)" fill="#8B5CF6" fillOpacity={0.15} stroke="#8B5CF6" strokeWidth={2.5} name="Sentient AI" />
                <Area type="monotone" dataKey="Base HVAC Energy (kWh)" fill="none" stroke="#64748B" strokeWidth={1.5} strokeDasharray="4 4" name="Baseline RBC" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Occupancy Curve Chart */}
        <div className={`bg-slate-900/40 border ${borderClass} p-6 rounded-xl lg:col-span-2 relative overflow-hidden`}>
          <h4 className={`text-xs font-bold uppercase tracking-widest ${subtextClass} mb-4`}>Building Occupancy Curves</h4>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={getOccupancyChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "rgba(255,255,255,0.03)" : "rgba(15, 23, 42, 0.05)"} />
                <XAxis dataKey="Hour" stroke="#475569" tickFormatter={(v) => `${Math.floor(v)}h`} className="text-[10px]" />
                <YAxis stroke="#475569" className="text-[10px]" />
                <Tooltip contentStyle={{ backgroundColor: darkMode ? "#0b0f1a" : "#ffffff", borderColor: darkMode ? "rgba(255,255,255,0.08)" : "#e2e8f0", color: darkMode ? "#e2e8f0" : "#0f172a" }} />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="Zone 1: Open Office" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Zone 2: Meeting Room" stroke="#22D3EE" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Zone 3: Executive Suite" stroke="#6366F1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSettingsView = () => (
    <div className={`${cardClass} space-y-8 animate-fade-in`}>
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400">
            <Settings size={22} />
          </div>
          <div>
            <h3 className={`text-sm font-black tracking-wide uppercase ${textClass}`}>System Settings & Bounds</h3>
            <p className="text-xs text-slate-500">Actuator thresholds & environmental boundaries</p>
          </div>
        </div>
        <button className="text-slate-500 hover:text-white cursor-pointer"><MoreVertical size={18} /></button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className={`p-6 bg-slate-900/40 border ${borderClass} rounded-xl space-y-4`}>
          <h4 className={`font-bold border-b ${borderClass} pb-2.5 text-sm ${textClass}`}>Thermal Safety Parameters</h4>
          
          <div className="space-y-3.5 text-xs font-mono-tech">
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">Cooling Protection Threshold:</span>
              <span className={textClass}>18.0°C - 30.0°C</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">Heating Protection Threshold:</span>
              <span className={textClass}>12.0°C - 22.0°C</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">Max Setpoint Ramp Limit:</span>
              <span className={textClass}>3.0°C/step</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">Minimum Temperature Deadband:</span>
              <span className={textClass}>1.0°C</span>
            </div>
          </div>
        </div>

        <div className={`p-6 bg-slate-900/40 border ${borderClass} rounded-xl space-y-4`}>
          <h4 className={`font-bold border-b ${borderClass} pb-2.5 text-sm ${textClass}`}>BMS Data Generator Info</h4>
          
          <div className="space-y-3.5 text-xs font-mono-tech">
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">Simulation Frequency:</span>
              <span className={textClass}>96 steps / 24 hours</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">Carbon stress hour peak:</span>
              <span className="text-amber-500 font-bold">12:00 - 15:00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">RC Model Capacitance:</span>
              <span className={textClass}>C_zone = 5.0e6 J/K</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-sans">RC Model Resistance:</span>
              <span className={textClass}>R_out = 0.05 K/W</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen ${darkMode ? "bg-[#0B0F19] text-[#E2E8F0]" : "bg-[#F8FAFC] text-slate-800"} flex flex-col relative overflow-hidden font-sans pb-16 transition-colors duration-300`}>
      
      {/* Background Soft Glow blobs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[5%] left-[25%] w-[45%] h-[45%] rounded-full bg-indigo-600/5 blur-[130px] animate-pulse-glow" />
        <div className="absolute bottom-[10%] right-[15%] w-[45%] h-[45%] rounded-full bg-cyan-600/5 blur-[130px] animate-pulse-glow" />
      </div>

      {/* Floating Header */}
      <header className={`relative z-20 max-w-[1200px] w-[92%] mx-auto mt-6 px-6 py-4 rounded-full flex items-center justify-between shadow-xl ${
        darkMode ? "bg-[#090C15]/85 border border-white/5" : "bg-white/95 border border-slate-200"
      }`}>
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/25">
            <Layers className="text-white h-4.5 w-4.5" />
          </div>
          <span className={`font-black text-sm tracking-wider uppercase ${textClass}`}>SentientBMS</span>
        </div>

        {/* Tab Options */}
        <nav className="flex items-center bg-black/5 border border-white/5 rounded-full p-0.5">
          {[
            { id: "Dashboard", label: "Dashboard", icon: <Sliders size={14} /> },
            { id: "Zones", label: "Zones", icon: <Building size={14} /> },
            { id: "Analytics", label: "Analytics", icon: <BarChart3 size={14} /> },
            { id: "Settings", label: "Settings", icon: <Settings size={14} /> }
          ].map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-1.5 px-4.5 py-2 rounded-full transition-all text-xs font-bold uppercase tracking-wider cursor-pointer ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-[0_0_15px_rgba(99,102,241,0.2)]"
                    : `${subtextClass} hover:text-white`
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Theme Controller Toggle & Status */}
        <div className="flex items-center gap-3">
          {/* Light/Dark Toggle Switch */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            title="Toggle Light/Dark Theme"
            className={`p-2.5 rounded-full border transition-all cursor-pointer flex items-center justify-center ${
              darkMode ? "bg-white/5 border-white/10 text-yellow-400 hover:bg-white/10" : "bg-slate-100 border-slate-200 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {darkMode ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          <span className="flex items-center gap-1.5 px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded-full text-[9px] font-black tracking-widest border border-indigo-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
            AI ACTIVE
          </span>
        </div>
      </header>

      {/* Floating HUD Operations Card */}
      <section className="relative z-10 max-w-[1200px] w-[92%] mx-auto mt-10">
        <div className={`${cardClass} flex flex-col lg:flex-row items-center justify-between gap-6 relative`}>
          <div className="space-y-1">
            <h1 className={`text-3xl font-black tracking-tight ${textClass}`}>Operations Center</h1>
            <p className={`text-xs ${subtextClass} font-medium`}>Telemetry overview and closed-loop strategy control</p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className={`flex items-center gap-3 px-4 py-2 ${bgClass} rounded-full text-xs font-mono-tech border ${borderClass} shadow-inner`}>
              <Clock size={14} className="text-slate-500" />
              <span className="font-bold text-cyan-500 text-sm">{buildingState.time_str}</span>
              <span className="text-[9px] font-bold text-slate-500 bg-white/5 px-2.5 py-0.5 rounded-full">
                STEP {buildingState.step}/96
              </span>
            </div>

            {/* Play controls */}
            <div className={`flex items-center ${bgClass} border ${borderClass} rounded-full p-0.5 shadow-inner`}>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                disabled={buildingState.step >= 96}
                className={`p-3 rounded-full transition-all outline-none cursor-pointer flex items-center justify-center ${
                  isPlaying ? "text-rose-500 bg-rose-500/10" : "text-slate-500 hover:bg-white/10"
                }`}
              >
                {isPlaying ? <Pause size={15} /> : <Play size={15} />}
              </button>

              <div className={`w-[1px] h-5 ${borderClass} mx-1`} />

              <button
                onClick={handleStep}
                disabled={isPlaying || buildingState.step >= 96}
                className="p-3 rounded-full text-slate-500 hover:bg-white/10 hover:text-indigo-600 transition-all outline-none cursor-pointer flex items-center justify-center"
              >
                <Activity size={15} />
              </button>

              <div className={`w-[1px] h-5 ${borderClass} mx-1`} />

              <button
                onClick={handleReset}
                className="p-3 rounded-full text-slate-500 hover:bg-white/10 hover:text-slate-200 transition-all outline-none cursor-pointer flex items-center justify-center"
              >
                <RotateCcw size={15} />
              </button>
            </div>

            {/* Outlined transparent amber button */}
            <button
              onClick={handleInjectViolation}
              disabled={violationQueued || buildingState.step >= 96}
              className={`px-4.5 py-3 text-xs font-extrabold uppercase tracking-wider rounded-full border transition-all cursor-pointer ${
                violationQueued
                  ? "bg-amber-500/10 text-amber-500 border-amber-500/20 cursor-not-allowed"
                  : "bg-transparent text-amber-500 border-amber-500/30 hover:bg-amber-500/10"
              }`}
            >
              ⚠️ Inject Fault
            </button>
          </div>
        </div>
      </section>

      {/* Connection / API Error Banner */}
      {errorMsg && (
        <section className="relative z-10 max-w-[1200px] w-[92%] mx-auto mt-6">
          <div className="bg-rose-500/10 border border-rose-500/25 text-rose-500 px-5 py-4 rounded-xl flex items-center gap-3 shadow-lg">
            <AlertOctagon size={20} className="shrink-0 animate-bounce" />
            <span className="text-xs font-bold leading-normal">{errorMsg}</span>
          </div>
        </section>
      )}

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-[1200px] w-[92%] mx-auto mt-10 relative z-10">
        {activeTab === "Dashboard" && renderDashboardView()}
        {activeTab === "Zones" && renderZonesView()}
        {activeTab === "Analytics" && renderAnalyticsView()}
        {activeTab === "Settings" && renderSettingsView()}
      </main>
    </div>
  );
}
