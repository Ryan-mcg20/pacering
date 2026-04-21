"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";

interface LiveGraphProps {
  bpm: number;
  className?: string;
}

export function LiveGraph({ bpm, className }: LiveGraphProps) {
  const [points, setPoints] = useState<number[]>([]);
  const svgWidth = 400;
  const svgHeight = 100;
  const maxPoints = 60;
  const animationRef = useRef<number | undefined>(undefined);
  const lastUpdateRef = useRef<number>(0);

  useEffect(() => {
    const updateInterval = 60000 / bpm / 4; // Update 4 times per heartbeat

    const animate = (timestamp: number) => {
      if (timestamp - lastUpdateRef.current >= updateInterval) {
        lastUpdateRef.current = timestamp;

        setPoints((prev) => {
          const newPoints = [...prev];
          const phase = (timestamp / (60000 / bpm)) % 1;

          let newValue: number;
          if (phase < 0.1) {
            // P wave
            newValue = 50 + Math.sin(phase * Math.PI * 10) * 10;
          } else if (phase < 0.15) {
            // PR segment
            newValue = 50;
          } else if (phase < 0.18) {
            // Q wave
            newValue = 50 - 8;
          } else if (phase < 0.25) {
            // R wave (spike)
            newValue = 50 - 45 * Math.sin((phase - 0.18) * Math.PI / 0.07);
          } else if (phase < 0.3) {
            // S wave
            newValue = 50 + 12;
          } else if (phase < 0.45) {
            // ST segment
            newValue = 50;
          } else if (phase < 0.6) {
            // T wave
            newValue = 50 + Math.sin((phase - 0.45) * Math.PI / 0.15) * 15;
          } else {
            // Baseline
            newValue = 50 + (Math.random() - 0.5) * 2;
          }

          newPoints.push(newValue);
          if (newPoints.length > maxPoints) {
            newPoints.shift();
          }
          return newPoints;
        });
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [bpm]);

  const pathD = points
    .map((point, index) => {
      const x = (index / maxPoints) * svgWidth;
      const y = point;
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className={className}
    >
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="w-full h-full"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ff1744" stopOpacity="0.2" />
            <stop offset="50%" stopColor="#ff1744" stopOpacity="1" />
            <stop offset="100%" stopColor="#ff1744" stopOpacity="1" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Grid lines */}
        {[...Array(5)].map((_, i) => (
          <line
            key={`h-${i}`}
            x1="0"
            y1={i * 25}
            x2={svgWidth}
            y2={i * 25}
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth="1"
          />
        ))}
        {[...Array(12)].map((_, i) => (
          <line
            key={`v-${i}`}
            x1={i * (svgWidth / 12)}
            y1="0"
            x2={i * (svgWidth / 12)}
            y2={svgHeight}
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth="1"
          />
        ))}

        {/* ECG line */}
        {points.length > 1 && (
          <path
            d={pathD}
            fill="none"
            stroke="url(#lineGradient)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#glow)"
          />
        )}

        {/* Trailing glow point */}
        {points.length > 0 && (
          <circle
            cx={(points.length / maxPoints) * svgWidth}
            cy={points[points.length - 1]}
            r="4"
            fill="#ff1744"
            filter="url(#glow)"
          />
        )}
      </svg>
    </motion.div>
  );
}
