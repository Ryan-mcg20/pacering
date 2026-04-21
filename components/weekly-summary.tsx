"use client";

import { motion } from "framer-motion";
import { GlassCard } from "./glass-card";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Activity,
  Heart,
  Clock,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface UserSettings {
  name: string;
  targetBpm: number;
  sensitivity: "low" | "medium" | "high";
  warningEnabled: boolean;
}

interface WeeklySummaryProps {
  settings: UserSettings;
  onBack: () => void;
}

const weeklyData = [
  { day: "Mon", avg: 68, min: 58, max: 95, spikes: 2 },
  { day: "Tue", avg: 72, min: 60, max: 110, spikes: 4 },
  { day: "Wed", avg: 65, min: 55, max: 88, spikes: 1 },
  { day: "Thu", avg: 70, min: 58, max: 92, spikes: 3 },
  { day: "Fri", avg: 74, min: 62, max: 118, spikes: 5 },
  { day: "Sat", avg: 66, min: 54, max: 85, spikes: 1 },
  { day: "Sun", avg: 64, min: 52, max: 82, spikes: 0 },
];

export function WeeklySummary({ settings, onBack }: WeeklySummaryProps) {
  const avgBpm = Math.round(
    weeklyData.reduce((sum, d) => sum + d.avg, 0) / weeklyData.length
  );
  const totalSpikes = weeklyData.reduce((sum, d) => sum + d.spikes, 0);
  const minBpm = Math.min(...weeklyData.map((d) => d.min));
  const maxBpm = Math.max(...weeklyData.map((d) => d.max));

  const getBarColor = (value: number) => {
    if (value > settings.targetBpm + 10) return "#ef4444";
    if (value > settings.targetBpm) return "#f59e0b";
    return "#22c55e";
  };

  return (
    <div className="min-h-screen bg-background p-4 pb-8">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4 mb-6"
      >
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/15 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-white" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-white">Weekly Summary</h1>
          <p className="text-sm text-muted-foreground">Past 7 days overview</p>
        </div>
      </motion.header>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Heart className="w-4 h-4 text-primary" />
            <span className="text-xs text-muted-foreground">Avg BPM</span>
          </div>
          <span className="text-3xl font-bold text-white">{avgBpm}</span>
          <div className="flex items-center gap-1 mt-1">
            {avgBpm <= settings.targetBpm ? (
              <>
                <TrendingDown className="w-3 h-3 text-green-400" />
                <span className="text-xs text-green-400">On target</span>
              </>
            ) : (
              <>
                <TrendingUp className="w-3 h-3 text-yellow-400" />
                <span className="text-xs text-yellow-400">Above target</span>
              </>
            )}
          </div>
        </GlassCard>

        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-red-400" />
            <span className="text-xs text-muted-foreground">Spikes</span>
          </div>
          <span className="text-3xl font-bold text-white">{totalSpikes}</span>
          <p className="text-xs text-muted-foreground mt-1">
            {totalSpikes < 10 ? "Low activity" : "Moderate activity"}
          </p>
        </GlassCard>

        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-muted-foreground">Lowest</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white">{minBpm}</span>
            <span className="text-sm text-muted-foreground">BPM</span>
          </div>
        </GlassCard>

        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-orange-400" />
            <span className="text-xs text-muted-foreground">Highest</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white">{maxBpm}</span>
            <span className="text-sm text-muted-foreground">BPM</span>
          </div>
        </GlassCard>
      </div>

      {/* Daily Average Chart */}
      <GlassCard className="p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">Daily Average</h3>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>7 days</span>
          </div>
        </div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weeklyData} barCategoryGap="20%">
              <XAxis
                dataKey="day"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }}
                domain={[40, 120]}
              />
              <Bar dataKey="avg" radius={[6, 6, 0, 0]}>
                {weeklyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.avg)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        {/* Legend */}
        <div className="flex items-center justify-center gap-4 mt-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-500" />
            <span className="text-xs text-muted-foreground">Normal</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-yellow-500" />
            <span className="text-xs text-muted-foreground">Elevated</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span className="text-xs text-muted-foreground">High</span>
          </div>
        </div>
      </GlassCard>

      {/* Spike Distribution */}
      <GlassCard className="p-4 mb-6">
        <h3 className="text-white font-semibold mb-4">Spike Distribution</h3>
        <div className="space-y-3">
          {weeklyData.map((day, index) => (
            <motion.div
              key={day.day}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center gap-3"
            >
              <span className="text-sm text-muted-foreground w-10">
                {day.day}
              </span>
              <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(day.spikes / 5) * 100}%` }}
                  transition={{ delay: index * 0.05 + 0.2, duration: 0.5 }}
                  className={`h-full rounded-full ${
                    day.spikes >= 4
                      ? "bg-red-500"
                      : day.spikes >= 2
                        ? "bg-yellow-500"
                        : "bg-green-500"
                  }`}
                />
              </div>
              <span className="text-sm text-white w-6 text-right">
                {day.spikes}
              </span>
            </motion.div>
          ))}
        </div>
      </GlassCard>

      {/* Range Overview */}
      <GlassCard className="p-4">
        <h3 className="text-white font-semibold mb-4">BPM Range by Day</h3>
        <div className="space-y-4">
          {weeklyData.map((day, index) => (
            <motion.div
              key={day.day}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: index * 0.05 }}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-muted-foreground">{day.day}</span>
                <span className="text-xs text-muted-foreground">
                  {day.min} - {day.max} BPM
                </span>
              </div>
              <div className="relative h-2 bg-white/10 rounded-full">
                <div
                  className="absolute h-full bg-gradient-to-r from-blue-500 via-green-500 to-red-500 rounded-full"
                  style={{
                    left: `${((day.min - 40) / 100) * 100}%`,
                    width: `${((day.max - day.min) / 100) * 100}%`,
                  }}
                />
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full border-2 border-primary"
                  style={{
                    left: `${((day.avg - 40) / 100) * 100}%`,
                  }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
