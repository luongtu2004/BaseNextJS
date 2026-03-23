'use client';

import { motion, useMotionValue, useTransform, animate, useInView } from 'framer-motion';
import { useEffect, useState, useRef } from 'react';

interface TypingTextProps {
  text: string;
  className?: string;
  delay?: number;
  stagger?: number;
  once?: boolean;
  showCursor?: boolean;
  onComplete?: () => void;
  start?: boolean;
}

export default function TypingText({
  text,
  className = "",
  delay = 0,
  stagger = 0.05,
  once = true,
  showCursor = true,
  onComplete,
  start = true
}: TypingTextProps) {
  const [isDone, setIsDone] = useState(false);
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));
  const displayText = useTransform(rounded, (latest) => text.slice(0, latest));

  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once });
  const hasStarted = useRef(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (isInView && start && !hasStarted.current) {
      hasStarted.current = true;
      const controls = animate(count, text.length, {
        duration: text.length * stagger,
        delay: delay,
        ease: "linear",
        onComplete: () => {
          setIsDone(true);
          onCompleteRef.current?.();
        }
      });
      return controls.stop;
    }
  }, [isInView, start, text.length, stagger, delay, count]);

  return (
    <span ref={containerRef} className={`inline ${className}`}>
      <motion.span>{displayText}</motion.span>
      {showCursor && (
        <motion.span
          animate={isDone ? { opacity: 0 } : { opacity: [1, 0] }}
          transition={isDone ? { duration: 0.2, delay: 1 } : { duration: 0.8, repeat: Infinity, ease: "linear" }}
          className="inline-block w-[3px] h-[1em] bg-primary ml-0.5 align-middle"
          style={{ display: isInView ? 'inline-block' : 'none' }}
        />
      )}
    </span>
  );
}
