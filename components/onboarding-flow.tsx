"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GlassCard } from "./glass-card";
import { Heart, ChevronRight, Activity, Bell } from "lucide-react";

interface UserSettings {
  name: string;
  targetBpm: number;
  sensitivity: "low" | "medium" | "high";
  warningEnabled: boolean;
}

interface OnboardingFlowProps {
  onComplete: (settings: UserSettings) => void;
}

export function OnboardingFlow({ onComplete }: OnboardingFlowProps) {
  const [step, setStep] = useState(1);
  const [settings, setSettings] = useState<UserSettings>({
    name: "",
    targetBpm: 70,
    sensitivity: "medium",
    warningEnabled: true,
  });

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 300 : -300,
      opacity: 0,
    }),
  };

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      onComplete(settings);
    }
  };

  const canProceed = () => {
    if (step === 1) return settings.name.trim().length > 0;
    return true;
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-8">
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === step
                  ? "w-8 bg-primary"
                  : i < step
                    ? "w-2 bg-primary/60"
                    : "w-2 bg-white/20"
              }`}
              layoutId={`dot-${i}`}
            />
          ))}
        </div>

        <AnimatePresence mode="wait" custom={step}>
          {step === 1 && (
            <motion.div
              key="step1"
              custom={1}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3, ease: "easeInOut" }}
            >
              <GlassCard className="text-center" animate={false}>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="w-20 h-20 mx-auto mb-6 rounded-full bg-primary/20 flex items-center justify-center"
                >
                  <Heart className="w-10 h-10 text-primary" />
                </motion.div>
                <h1 className="text-2xl font-bold text-white mb-2">
                  Welcome to PacerRing
                </h1>
                <p className="text-muted-foreground mb-8">
                  Who are we monitoring today?
                </p>
                <input
                  type="text"
                  placeholder="Enter your name"
                  value={settings.name}
                  onChange={(e) =>
                    setSettings({ ...settings, name: e.target.value })
                  }
                  className="w-full px-4 py-3 bg-white/10 border border-white/10 rounded-xl text-white placeholder:text-white/40 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                />
              </GlassCard>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              custom={1}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3, ease: "easeInOut" }}
            >
              <GlassCard className="text-center" animate={false}>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="w-20 h-20 mx-auto mb-6 rounded-full bg-primary/20 flex items-center justify-center"
                >
                  <Activity className="w-10 h-10 text-primary" />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Target Resting BPM
                </h2>
                <p className="text-muted-foreground mb-8">
                  Set your healthy resting heart rate
                </p>
                <div className="flex items-center justify-center gap-4 mb-4">
                  <button
                    onClick={() =>
                      setSettings({
                        ...settings,
                        targetBpm: Math.max(40, settings.targetBpm - 5),
                      })
                    }
                    className="w-12 h-12 rounded-full bg-white/10 text-white text-2xl font-bold hover:bg-white/20 transition-colors"
                  >
                    -
                  </button>
                  <div className="w-32">
                    <span className="text-6xl font-bold text-white">
                      {settings.targetBpm}
                    </span>
                    <span className="text-muted-foreground text-lg ml-1">
                      BPM
                    </span>
                  </div>
                  <button
                    onClick={() =>
                      setSettings({
                        ...settings,
                        targetBpm: Math.min(120, settings.targetBpm + 5),
                      })
                    }
                    className="w-12 h-12 rounded-full bg-white/10 text-white text-2xl font-bold hover:bg-white/20 transition-colors"
                  >
                    +
                  </button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Normal resting: 60-100 BPM
                </p>
              </GlassCard>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              custom={1}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3, ease: "easeInOut" }}
            >
              <GlassCard className="text-center" animate={false}>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="w-20 h-20 mx-auto mb-6 rounded-full bg-primary/20 flex items-center justify-center"
                >
                  <Bell className="w-10 h-10 text-primary" />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Alert Settings
                </h2>
                <p className="text-muted-foreground mb-8">
                  Configure spike detection sensitivity
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground block mb-3">
                      Spike Sensitivity
                    </label>
                    <div className="flex gap-2">
                      {(["low", "medium", "high"] as const).map((level) => (
                        <button
                          key={level}
                          onClick={() =>
                            setSettings({ ...settings, sensitivity: level })
                          }
                          className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium capitalize transition-all ${
                            settings.sensitivity === level
                              ? "bg-primary text-white"
                              : "bg-white/10 text-white/60 hover:bg-white/15"
                          }`}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                    <span className="text-white">Warning Threshold</span>
                    <button
                      onClick={() =>
                        setSettings({
                          ...settings,
                          warningEnabled: !settings.warningEnabled,
                        })
                      }
                      className={`relative w-14 h-8 rounded-full transition-colors ${
                        settings.warningEnabled ? "bg-primary" : "bg-white/20"
                      }`}
                    >
                      <motion.div
                        className="absolute top-1 w-6 h-6 bg-white rounded-full"
                        animate={{
                          left: settings.warningEnabled ? "calc(100% - 28px)" : "4px",
                        }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      />
                    </button>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Next button */}
        <motion.button
          onClick={handleNext}
          disabled={!canProceed()}
          className={`w-full mt-6 py-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all ${
            canProceed()
              ? "bg-primary text-white hover:bg-primary/90"
              : "bg-white/10 text-white/30 cursor-not-allowed"
          }`}
          whileTap={canProceed() ? { scale: 0.98 } : {}}
        >
          {step === 3 ? "Start Monitoring" : "Continue"}
          <ChevronRight className="w-5 h-5" />
        </motion.button>
      </div>
    </div>
  );
}
