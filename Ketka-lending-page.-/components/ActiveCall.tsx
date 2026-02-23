import React, { useEffect, useState } from 'react';
import { BusinessConfig } from '../types';
import { Visualizer } from './Visualizer';
import { GeminiLiveService } from '../services/geminiLive';
import { motion } from 'framer-motion';

interface ActiveCallProps {
  config: BusinessConfig;
  onEndCall: () => void;
  service: GeminiLiveService;
}

export const ActiveCall: React.FC<ActiveCallProps> = ({ config, onEndCall, service }) => {
  const [volume, setVolume] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    service.onVolumeChange = (vol) => {
      setVolume(vol);
    };

    const interval = setInterval(() => {
      setDuration(prev => prev + 1);
    }, 1000);

    return () => {
      clearInterval(interval);
      service.onVolumeChange = null;
    };
  }, [service]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center justify-center w-full h-full px-4 py-6"
    >
      {/* Minimal Header */}
      <div className="text-center mb-8 relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 border border-signal bg-signal/10 text-signal font-mono text-[10px] font-bold uppercase tracking-widest mb-3">
          <span className="w-2 h-2 bg-signal animate-pulse"></span>
          LIVE
        </div>
        <p className="font-mono text-[10px] text-dark/50 uppercase tracking-widest">{config.businessName}</p>
      </div>

      {/* Compact Visualizer */}
      <div className="relative w-[140px] h-[140px] md:w-[200px] md:h-[200px] flex items-center justify-center mb-4">
        <Visualizer isActive={true} volume={volume} />
      </div>

      {/* Timer */}
      <p className="text-dark font-mono text-4xl md:text-5xl font-bold tracking-tighter mb-8 relative z-10">{formatTime(duration)}</p>

      {/* Speaking indicator */}
      <p className="font-mono text-[10px] text-dark/70 uppercase tracking-widest mb-8 relative z-10">Speaking with {config.firstName}</p>

      {/* End Call Button - Brutalist */}
      <button
        onClick={onEndCall}
        className="w-16 h-16 md:w-20 md:h-20 bg-signal hover:bg-signal/90 border border-dark border-b-4 border-r-4 flex items-center justify-center transition-all active:border-b active:border-r active:translate-y-[3px] active:translate-x-[3px] group relative z-10"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 md:h-8 md:w-8 text-paper group-hover:scale-90 transition-transform" viewBox="0 0 20 20" fill="currentColor">
          <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
        </svg>
      </button>

      <p className="font-mono text-[10px] text-dark/40 uppercase tracking-widest mt-4 relative z-10">Tap to end call</p>

      {/* Tip - Brutalist Callout */}
      <div className="mt-12 px-4 py-3 bg-paper border border-dark border-l-4 border-l-signal max-w-xs text-center relative z-10 shadow-[2px_2px_0px_#111111]">
        <p className="font-mono text-[10px] text-dark/70 tracking-tight">
          Try: "Book an appointment" or "What are your prices?"
        </p>
      </div>
    </motion.div>
  );
};
