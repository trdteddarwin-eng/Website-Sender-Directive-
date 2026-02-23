import React, { useEffect, useRef } from 'react';

interface VisualizerProps {
  isActive: boolean;
  volume: number; // 0 to 1
}

export const Visualizer: React.FC<VisualizerProps> = ({ isActive, volume }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let hue = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Dynamic center circle size
      const baseRadius = 50;
      const dynamicRadius = baseRadius + (volume * 80); // Grows with volume
      
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Draw glow
      const gradient = ctx.createRadialGradient(centerX, centerY, baseRadius * 0.5, centerX, centerY, dynamicRadius * 1.5);
      gradient.addColorStop(0, `hsla(${hue}, 80%, 60%, 0.8)`);
      gradient.addColorStop(0.5, `hsla(${hue}, 80%, 60%, 0.2)`);
      gradient.addColorStop(1, `hsla(${hue}, 80%, 60%, 0)`);

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, dynamicRadius * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // Draw Core
      ctx.fillStyle = `hsla(${hue + 30}, 90%, 95%, 1)`;
      ctx.beginPath();
      ctx.arc(centerX, centerY, isActive ? baseRadius + (volume * 10) : baseRadius, 0, Math.PI * 2);
      ctx.fill();

      // Ripple effect lines
      if (isActive && volume > 0.05) {
         ctx.strokeStyle = `hsla(${hue}, 70%, 70%, 0.5)`;
         ctx.lineWidth = 2;
         for(let i=1; i<=3; i++) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, dynamicRadius + (i * 20), 0, Math.PI * 2);
            ctx.stroke();
         }
      }

      hue = (hue + 0.5) % 360;
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
