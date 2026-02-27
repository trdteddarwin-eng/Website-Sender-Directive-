import React, { useEffect, useRef } from 'react';

interface VisualizerProps {
  isActive: boolean;
  volume: number; // 0 to 1
}

const SIGNAL_RED = '#E63B2E';
const DARK = '#111111';
const BAR_COUNT = 10;

export const Visualizer: React.FC<VisualizerProps> = ({ isActive, volume }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const smoothedVolumeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let pulsePhase = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Smooth volume with exponential decay
      smoothedVolumeRef.current = smoothedVolumeRef.current * 0.85 + volume * 0.15;
      const sv = smoothedVolumeRef.current;

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const baseRadius = 50;

      // Central circle with subtle pulse
      pulsePhase += 0.03;
      const pulseScale = 1 + (isActive ? Math.sin(pulsePhase) * 0.05 * (1 + sv) : 0);
      const coreRadius = baseRadius * pulseScale;

      // Glow behind center
      const glow = ctx.createRadialGradient(centerX, centerY, coreRadius * 0.5, centerX, centerY, coreRadius * 2);
      glow.addColorStop(0, `rgba(230, 59, 46, ${0.15 + sv * 0.2})`);
      glow.addColorStop(1, 'rgba(230, 59, 46, 0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreRadius * 2, 0, Math.PI * 2);
      ctx.fill();

      // Central filled circle
      ctx.fillStyle = DARK;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreRadius, 0, Math.PI * 2);
      ctx.fill();

      // Inner ring accent
      ctx.strokeStyle = SIGNAL_RED;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreRadius + 3, 0, Math.PI * 2);
      ctx.stroke();

      // Radial bar segments
      if (isActive) {
        const barInnerRadius = coreRadius + 10;
        const maxBarHeight = 60;
        const barWidth = (Math.PI * 2) / BAR_COUNT - 0.08; // gap between bars

        for (let i = 0; i < BAR_COUNT; i++) {
          const angle = (i / BAR_COUNT) * Math.PI * 2 - Math.PI / 2;

          // Each bar has slightly different height based on volume + pseudo-random variation
          const variation = Math.sin(pulsePhase * 2 + i * 1.3) * 0.3 + 0.7;
          const barHeight = maxBarHeight * sv * variation;

          if (barHeight < 2) continue;

          const outerRadius = barInnerRadius + barHeight;

          ctx.beginPath();
          ctx.arc(centerX, centerY, barInnerRadius, angle, angle + barWidth);
          ctx.arc(centerX, centerY, outerRadius, angle + barWidth, angle, true);
          ctx.closePath();

          // Gradient from signal red (base) to dark (tip)
          const opacity = 0.6 + sv * 0.4;
          ctx.fillStyle = `rgba(230, 59, 46, ${opacity})`;
          ctx.fill();
        }
      }

      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [isActive, volume]);

  return (
    <canvas
      ref={canvasRef}
      width={400}
      height={400}
      className="w-full max-w-[400px] h-auto mx-auto"
    />
  );
};
