'use client';

import { useEffect, useRef } from 'react';

// ─── Config ────────────────────────────────────────────────────────────────────
const PRIMARY_HEX = '#00B14F';
const ROTATION_SPEED = 0.0012;
const SPRING_STIFFNESS = 0.05;
const DAMPING = 0.90;

function getParticleCount(): number {
  if (typeof navigator === 'undefined') return 550;
  const cores = (navigator as any).hardwareConcurrency ?? 4;
  if (cores <= 2) return 250;
  if (cores <= 4) return 400;
  return 550;
}

function rand(a: number, b: number) { return a + Math.random() * (b - a); }

// ─── Particle ─────────────────────────────────────────────────────────────────
class Particle {
  // Target position on orbital path (relative to hub)
  orbitAngle: number;
  orbitRx: number;
  orbitRy: number;

  // Physics state
  x: number;
  y: number;
  vx: number;
  vy: number;

  // Visual properties
  size: number;
  length: number;
  opacity: number;
  angle: number; // calculated pointing to hub

  constructor(cw: number, ch: number, hx: number, hy: number) {
    // Target orbit settings
    const rBase = Math.pow(Math.random(), 1.2) * Math.min(cw, ch) * 0.8;
    this.orbitRx = rBase;
    this.orbitRy = rBase * 0.8;
    this.orbitAngle = Math.random() * Math.PI * 2;

    // "Converging Rays" Entrance: Spawn far away from the hub
    // Start at random edges or far out
    const spawnDist = Math.max(cw, ch) * 1.5;
    const spawnAngle = Math.random() * Math.PI * 2;

    this.x = hx + Math.cos(spawnAngle) * spawnDist;
    this.y = hy + Math.sin(spawnAngle) * spawnDist;

    this.vx = 0;
    this.vy = 0;

    // Elongated shape props
    this.size = rand(1, 2.5);
    this.length = rand(8, 20);
    this.opacity = 0; // Start invisible and fade in
    this.angle = 0;
  }

  update(hx: number, hy: number) {
    // 1. Orbital update
    this.orbitAngle += ROTATION_SPEED;

    // Fade in during entrance
    if (this.opacity < 0.6) this.opacity += 0.005;

    // Static bloom effect
    const tx = hx + Math.cos(this.orbitAngle) * this.orbitRx;
    const ty = hy + Math.sin(this.orbitAngle) * this.orbitRy;

    // 2. Point towards hub
    this.angle = Math.atan2(hy - this.y, hx - this.x);

    // 3. Physics (Spring to target orbit position)
    const ax = (tx - this.x) * SPRING_STIFFNESS;
    const ay = (ty - this.y) * SPRING_STIFFNESS;

    this.vx += ax;
    this.vy += ay;

    this.vx += ax;
    this.vy += ay;

    this.vx *= DAMPING;
    this.vy *= DAMPING;
    this.x += this.vx;
    this.y += this.vy;
  }

  draw(ctx: CanvasRenderingContext2D) {
    const opacityHex = Math.round(this.opacity * 255).toString(16).padStart(2, '0');
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.angle);
    ctx.fillStyle = PRIMARY_HEX + opacityHex;

    // Draw elongated shape (dash)
    const r = this.size / 2;
    ctx.beginPath();
    // Rounded rect: -length to 0 so "head" points to hub
    ctx.roundRect(-this.length, -r, this.length, this.size, r);
    ctx.fill();
    ctx.restore();
  }
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let particles: Particle[] = [];
    let width = 0;
    let height = 0;

    // Static hub position - will center on right column
    let hubX = width * 0.75; // Default fallback to right side
    let hubY = height * 0.5; // Default fallback to vertical center

    let animationFrameId: number;

    const init = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;

      // Try to find the visual column container to center exactly on it
      const visualElements = document.querySelectorAll('.hero-visual-container');
      if (visualElements.length > 0) {
        const visualRect = visualElements[0].getBoundingClientRect();
        const canvasRect = canvas.getBoundingClientRect();

        // Calculate center relative to canvas
        hubX = (visualRect.left + visualRect.width / 2) - canvasRect.left;
        hubY = (visualRect.top + visualRect.height / 2) - canvasRect.top;
      } else {
        // Fallback for smaller screens where the right column might be hidden
        hubX = width / 2;
        hubY = height / 2;
      }

      const count = getParticleCount();
      particles = [];
      for (let i = 0; i < count; i++) {
        particles.push(new Particle(width, height, hubX, hubY));
      }
    };

    const handleResize = () => {
      init();
    };

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      particles.forEach(p => {
        p.update(hubX, hubY);
        p.draw(ctx);
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    window.addEventListener('resize', handleResize);

    init();
    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 z-0 pointer-events-none"
    />
  );
}
