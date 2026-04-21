"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  animate?: boolean;
}

export function GlassCard({
  children,
  className,
  animate = true,
}: GlassCardProps) {
  const Wrapper = animate ? motion.div : "div";
  const animateProps = animate
    ? {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.4, ease: "easeOut" },
      }
    : {};

  return (
    <Wrapper
      className={cn("glass-card p-6", className)}
      {...(animateProps as object)}
    >
      {children}
    </Wrapper>
  );
}
