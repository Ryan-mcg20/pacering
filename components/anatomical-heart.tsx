"use client";

import { motion } from "framer-motion";
import { useEffect, useState, useRef } from "react";

interface AnatomicalHeartProps {
  bpm: number;
  size?: number;
}

export function AnatomicalHeart({ bpm, size = 280 }: AnatomicalHeartProps) {
  const [scale, setScale] = useState(1);
  const animationRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    const beatDuration = (60 / bpm) * 1000; // in ms

    let phase = 0;
    let lastTime = performance.now();

    const animate = (currentTime: number) => {
      if (!isMountedRef.current) return;

      const elapsed = currentTime - lastTime;
      phase += elapsed;

      // Lub-Dub cycle
      const cyclePosition = (phase % beatDuration) / beatDuration;

      let newScale: number;
      if (cyclePosition < 0.1) {
        // Lub - quick contraction (0-10%)
        newScale = 1 - 0.1 * (cyclePosition / 0.1);
      } else if (cyclePosition < 0.25) {
        // Dub - elastic rebound (10-25%)
        const reboundProgress = (cyclePosition - 0.1) / 0.15;
        newScale = 0.9 + 0.25 * reboundProgress;
      } else {
        // Settle back (25-100%)
        const settleProgress = (cyclePosition - 0.25) / 0.75;
        newScale = 1.15 - 0.15 * settleProgress;
      }

      setScale(newScale);
      lastTime = currentTime;
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      isMountedRef.current = false;
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [bpm]);

  return (
    <motion.div
      className="relative heart-glow"
      style={{ width: size, height: size, transform: `scale(${scale})` }}
    >
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full"
        style={{ filter: "drop-shadow(0 0 30px rgba(220, 20, 60, 0.6))" }}
      >
        <defs>
          {/* Main heart gradient */}
          <radialGradient
            id="heartGradient"
            cx="50%"
            cy="40%"
            r="60%"
            fx="30%"
            fy="30%"
          >
            <stop offset="0%" stopColor="#ff4d6d" />
            <stop offset="30%" stopColor="#dc143c" />
            <stop offset="60%" stopColor="#b91c3c" />
            <stop offset="100%" stopColor="#7f1d2d" />
          </radialGradient>

          {/* Highlight gradient for 3D depth */}
          <radialGradient id="highlightGradient" cx="30%" cy="25%" r="40%">
            <stop offset="0%" stopColor="rgba(255, 200, 200, 0.5)" />
            <stop offset="100%" stopColor="rgba(255, 200, 200, 0)" />
          </radialGradient>

          {/* Deep shadow gradient */}
          <radialGradient id="shadowGradient" cx="70%" cy="70%" r="50%">
            <stop offset="0%" stopColor="rgba(50, 0, 0, 0)" />
            <stop offset="100%" stopColor="rgba(50, 0, 0, 0.4)" />
          </radialGradient>

          {/* Vein pattern */}
          <linearGradient id="veinGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b0000" />
            <stop offset="100%" stopColor="#5c0a0a" />
          </linearGradient>
        </defs>

        {/* Main heart shape - anatomical style */}
        <path
          d="M50 88
             C25 70 8 55 8 38
             C8 22 20 12 35 12
             C42 12 48 16 50 22
             C52 16 58 12 65 12
             C80 12 92 22 92 38
             C92 55 75 70 50 88Z"
          fill="url(#heartGradient)"
        />

        {/* Highlight overlay */}
        <path
          d="M50 88
             C25 70 8 55 8 38
             C8 22 20 12 35 12
             C42 12 48 16 50 22
             C52 16 58 12 65 12
             C80 12 92 22 92 38
             C92 55 75 70 50 88Z"
          fill="url(#highlightGradient)"
        />

        {/* Shadow overlay */}
        <path
          d="M50 88
             C25 70 8 55 8 38
             C8 22 20 12 35 12
             C42 12 48 16 50 22
             C52 16 58 12 65 12
             C80 12 92 22 92 38
             C92 55 75 70 50 88Z"
          fill="url(#shadowGradient)"
        />

        {/* Left atrium detail */}
        <ellipse
          cx="32"
          cy="28"
          rx="12"
          ry="10"
          fill="none"
          stroke="#9b111e"
          strokeWidth="0.5"
          opacity="0.6"
        />

        {/* Right atrium detail */}
        <ellipse
          cx="68"
          cy="28"
          rx="12"
          ry="10"
          fill="none"
          stroke="#9b111e"
          strokeWidth="0.5"
          opacity="0.6"
        />

        {/* Center crease / septum */}
        <path
          d="M50 25 Q48 50 50 75"
          fill="none"
          stroke="#7f1d2d"
          strokeWidth="1"
          opacity="0.5"
        />

        {/* Aorta base indication */}
        <ellipse
          cx="50"
          cy="18"
          rx="8"
          ry="4"
          fill="url(#veinGradient)"
          opacity="0.7"
        />

        {/* Pulmonary artery hints */}
        <path
          d="M35 15 Q30 8 25 10"
          fill="none"
          stroke="#8b0000"
          strokeWidth="2"
          strokeLinecap="round"
          opacity="0.6"
        />
        <path
          d="M65 15 Q70 8 75 10"
          fill="none"
          stroke="#8b0000"
          strokeWidth="2"
          strokeLinecap="round"
          opacity="0.6"
        />

        {/* Surface veins */}
        <path
          d="M30 35 Q35 45 32 55"
          fill="none"
          stroke="#5c1a1a"
          strokeWidth="0.8"
          opacity="0.4"
        />
        <path
          d="M70 35 Q65 45 68 55"
          fill="none"
          stroke="#5c1a1a"
          strokeWidth="0.8"
          opacity="0.4"
        />
        <path
          d="M45 40 Q50 55 48 65"
          fill="none"
          stroke="#5c1a1a"
          strokeWidth="0.6"
          opacity="0.3"
        />

        {/* Specular highlights for wet/organic look */}
        <ellipse cx="28" cy="32" rx="4" ry="3" fill="white" opacity="0.15" />
        <ellipse cx="38" cy="25" rx="2" ry="1.5" fill="white" opacity="0.1" />
      </svg>
    </motion.div>
  );
}
