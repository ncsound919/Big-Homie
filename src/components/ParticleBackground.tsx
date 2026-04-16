'use client';

import { useEffect, useRef, useCallback } from 'react';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

export default function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const animationRef = useRef<number>(0);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  const initNodes = useCallback((width: number, height: number) => {
    const count = Math.min(Math.floor((width * height) / 15000), 80);
    const colors = [
      'oklch(0.65 0.2 280 / 40%)',
      'oklch(0.65 0.18 190 / 35%)',
      'oklch(0.6 0.15 160 / 30%)',
      'oklch(0.7 0.15 330 / 25%)',
    ];
    const nodes: Node[] = [];
    for (let i = 0; i < count; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2.5 + 1,
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }
    return nodes;
  }, []);

  const draw = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, nodes: Node[]) => {
    ctx.clearRect(0, 0, width, height);
    const connectionDistance = 150;
    const connectionDistSq = connectionDistance * connectionDistance;
    const mouseInfluence = 200;
    const mouseInfluenceSq = mouseInfluence * mouseInfluence;

    // Update positions in-place for performance (nodes array is already owned by ref)
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      node.x += node.vx;
      node.y += node.vy;

      // Bounce off edges
      if (node.x < 0 || node.x > width) node.vx *= -1;
      if (node.y < 0 || node.y > height) node.vy *= -1;

      // Mouse repulsion — avoid sqrt unless within squared range
      const dx = node.x - mouseRef.current.x;
      const dy = node.y - mouseRef.current.y;
      const distSq = dx * dx + dy * dy;
      if (distSq < mouseInfluenceSq && distSq > 0) {
        const dist = Math.sqrt(distSq);
        const force = (mouseInfluence - dist) / mouseInfluence;
        node.vx += (dx / dist) * force * 0.02;
        node.vy += (dy / dist) * force * 0.02;
      }

      // Dampen velocity
      node.vx *= 0.999;
      node.vy *= 0.999;

      // Keep within bounds
      node.x = Math.max(0, Math.min(width, node.x));
      node.y = Math.max(0, Math.min(height, node.y));
    }

    // Draw connections — use squared distance to avoid sqrt per pair
    ctx.lineWidth = 0.5;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const distSq = dx * dx + dy * dy;

        if (distSq < connectionDistSq) {
          const dist = Math.sqrt(distSq);
          const opacity = (1 - dist / connectionDistance) * 0.15;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = `oklch(0.65 0.2 280 / ${opacity})`;
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    for (const node of nodes) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.fill();
    }
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      if (nodesRef.current.length === 0) {
        nodesRef.current = initNodes(canvas.width, canvas.height);
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!prefersReducedMotion) {
      const animate = () => {
        draw(ctx, canvas.width, canvas.height, nodesRef.current);
        animationRef.current = requestAnimationFrame(animate);
      };
      animate();

      // Pause animation when tab is hidden to save CPU
      const handleVisibility = () => {
        if (document.hidden) {
          if (animationRef.current) cancelAnimationFrame(animationRef.current);
        } else {
          animate();
        }
      };
      document.addEventListener('visibilitychange', handleVisibility);

      return () => {
        window.removeEventListener('resize', resize);
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseleave', handleMouseLeave);
        document.removeEventListener('visibilitychange', handleVisibility);
        if (animationRef.current) cancelAnimationFrame(animationRef.current);
      };
    } else {
      draw(ctx, canvas.width, canvas.height, nodesRef.current);

      return () => {
        window.removeEventListener('resize', resize);
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseleave', handleMouseLeave);
      };
    }
  }, [initNodes, draw]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden="true"
    />
  );
}
