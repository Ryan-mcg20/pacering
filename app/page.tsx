"use client";

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { OnboardingFlow } from "@/components/onboarding-flow";
import { MonitorScreen } from "@/components/monitor-screen";
import { WeeklySummary } from "@/components/weekly-summary";

interface UserSettings {
  name: string;
  targetBpm: number;
  sensitivity: "low" | "medium" | "high";
  warningEnabled: boolean;
}

type Screen = "onboarding" | "monitor" | "summary";

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("onboarding");
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Check for existing settings in sessionStorage (not localStorage for persistence)
    const savedSettings = sessionStorage.getItem("pacering-settings");
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
      setCurrentScreen("monitor");
    }
    setIsLoaded(true);
  }, []);

  const handleOnboardingComplete = (userSettings: UserSettings) => {
    setSettings(userSettings);
    sessionStorage.setItem("pacering-settings", JSON.stringify(userSettings));
    setCurrentScreen("monitor");
  };

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading PacerRing...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <AnimatePresence mode="wait">
        {currentScreen === "onboarding" && (
          <motion.div
            key="onboarding"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <OnboardingFlow onComplete={handleOnboardingComplete} />
          </motion.div>
        )}

        {currentScreen === "monitor" && settings && (
          <motion.div
            key="monitor"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <MonitorScreen
              settings={settings}
              onShowSummary={() => setCurrentScreen("summary")}
            />
          </motion.div>
        )}

        {currentScreen === "summary" && settings && (
          <motion.div
            key="summary"
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <WeeklySummary
              settings={settings}
              onBack={() => setCurrentScreen("monitor")}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
