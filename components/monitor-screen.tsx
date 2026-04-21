"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { AnatomicalHeart } from "./anatomical-heart";
import { GlassCard } from "./glass-card";
import { LiveGraph } from "./live-graph";
import {
  Activity,
  Shield,
  ShieldAlert,
  TrendingUp,
  Zap,
  BarChart3,
  Settings,
} from "lucide-react";

interface UserSettings {
  name: string;
  targetBpm: number;
  sensitivity: "low" | "medium" | "high";
  warningEnabled: boolean;
}

interface MonitorScreenProps {
  settings: UserSettings;
  onShowSummary: () => void;
}

export function MonitorScreen({ settings, onShowSummary }: MonitorScreenProps) {
  const [currentBpm, setCurrentBpm] = useState(settings.targetBpm);
  const [hrv, setHrv] = useState(45);
  const [simulatorActive, setSimulatorActive] = useState(false);
  const [isSpike, setIsSpike] = useState(false);

  const sensitivityThresholds = {
    low: 40,
    medium: 30,
    high: 20,
  };

  const threshold = sensitivityThresholds[settings.sensitivity];
  const isWarning =
    settings.warningEnabled && currentBpm > settings.targetBpm + threshold;

  const getSafetyStatus = useCallback(() => {
    if (currentBpm > settings.targetBpm + threshold) {
      return { label: "Elevated", color: "text-red-400", icon: ShieldAlert };
    }
    if (currentBpm > settings.targetBpm + threshold / 2) {
      return { label: "Caution", color: "text-yellow-400", icon: Shield };
    }
    return { label: "Normal", color: "text-green-400", icon: Shield };
  }, [currentBpm, settings.targetBpm, threshold]);

  // Simulator effect
  useEffect(() => {
    if (!simulatorActive) return;

    const interval = setInterval(() => {
      setCurrentBpm((prev) => {
        // Random chance of spike
        if (Math.random() < 0.05 && !isSpike) {
          setIsSpike(true);
          return Math.min(180, prev + Math.random() * 40 + 20);
        }

        // If spiking, gradually return to normal
        if (isSpike) {
          if (prev <= settings.targetBpm + 10) {
            setIsSpike(false);
            return prev;
          }
          return prev - Math.random() * 8 - 2;
        }

        // Normal fluctuation around target
        const fluctuation = (Math.random() - 0.5) * 6;
        const newBpm = prev + fluctuation;
        return Math.max(
          settings.targetBpm - 15,
          Math.min(settings.targetBpm + 15, newBpm)
        );
      });

      // Update HRV
      setHrv((prev) => {
        const fluctuation = (Math.random() - 0.5) * 10;
        return Math.max(20, Math.min(80, prev + fluctuation));
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [simulatorActive, isSpike, settings.targetBpm]);

  const safetyStatus = getSafetyStatus();
  const StatusIcon = safetyStatus.icon;

  return (
    <div className="min-h-screen bg-background p-4 pb-24">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-6"
      >
        <div>
          <p className="text-muted-foreground text-sm">Good evening,</p>
          <h1 className="text-xl font-bold text-white">{settings.name}</h1>
        </div>
        <button
          onClick={onShowSummary}
          className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/15 transition-colors"
        >
          <BarChart3 className="w-5 h-5 text-white" />
        </button>
      </motion.header>

      {/* Warning Banner */}
      {isWarning && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-4 p-3 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center gap-3"
        >
          <ShieldAlert className="w-5 h-5 text-red-400" />
          <span className="text-red-300 text-sm font-medium">
            Heart rate elevated above threshold
          </span>
        </motion.div>
      )}

      {/* Main Heart Display */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col items-center justify-center py-8"
      >
        <AnatomicalHeart bpm={currentBpm} size={240} />

        <motion.div
          className="mt-6 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-baseline justify-center gap-1">
            <span
              className={`text-7xl font-bold ${isWarning ? "text-red-400" : "text-white"}`}
            >
              {Math.round(currentBpm)}
            </span>
            <span className="text-2xl text-muted-foreground">BPM</span>
          </div>
          <p className="text-muted-foreground text-sm mt-1">
            Target: {settings.targetBpm} BPM
          </p>
        </motion.div>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-primary" />
            <span className="text-xs text-muted-foreground">HRV</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white">
              {Math.round(hrv)}
            </span>
            <span className="text-sm text-muted-foreground">ms</span>
          </div>
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp className="w-3 h-3 text-green-400" />
            <span className="text-xs text-green-400">Good variability</span>
          </div>
        </GlassCard>

        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <StatusIcon className={`w-4 h-4 ${safetyStatus.color}`} />
            <span className="text-xs text-muted-foreground">Safety Status</span>
          </div>
          <span className={`text-2xl font-bold ${safetyStatus.color}`}>
            {safetyStatus.label}
          </span>
          <p className="text-xs text-muted-foreground mt-1">
            Threshold: +{threshold} BPM
          </p>
        </GlassCard>
      </div>

      {/* Live Graph */}
      <GlassCard className="p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-sm text-muted-foreground">Live ECG</span>
          </div>
          <Zap className="w-4 h-4 text-primary" />
        </div>
        <LiveGraph bpm={currentBpm} className="h-24" />
      </GlassCard>

      {/* Simulator Toggle */}
      <GlassCard className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-white font-medium">Simulator Mode</p>
              <p className="text-xs text-muted-foreground">
                Simulate realistic BPM fluctuations
              </p>
            </div>
          </div>
          <button
            onClick={() => setSimulatorActive(!simulatorActive)}
            className={`relative w-14 h-8 rounded-full transition-colors ${
              simulatorActive ? "bg-primary" : "bg-white/20"
            }`}
          >
            <motion.div
              className="absolute top-1 w-6 h-6 bg-white rounded-full"
              animate={{
                left: simulatorActive ? "calc(100% - 28px)" : "4px",
              }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          </button>
        </div>
      </GlassCard>
    </div>
  );
}
