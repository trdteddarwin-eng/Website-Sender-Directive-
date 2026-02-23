import React, { useEffect, useState } from 'react';
import { BusinessConfig } from '../types';
import { Visualizer } from './Visualizer';
import { GeminiLiveService } from '../services/geminiLive';
import { motion } from 'framer-motion';
import Cal, { getCalApi } from "@calcom/embed-react";

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

    // Simple timer for call duration
    const interval = setInterval(() => {
      setDuration(prev => prev + 1);
    }, 1000);

    return () => {
      clearInterval(interval);
      service.onVolumeChange = null;
    };
  }, [service]);

  useEffect(() => {
    (async function () {
      const cal = await getCalApi({ "namespace": "30min" });
      cal("ui", { "styles": { "branding": { "brandColor": "#7d3131" } }, "hideEventTypeDetails": false, "layout": "month_view" });
    })();
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col lg:flex-row items-center justify-center min-h-[600px] w-full max-w-6xl mx-auto gap-8 p-4"
    >
      {/* Left Side: Visualizer and Controls */}
      <div className="flex flex-col items-center justify-center w-full lg:w-1/2">
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold tracking-wider animate-pulse">
            LIVE DEMO
          </div>
          <h2 className="text-2xl font-semibold text-white">{config.businessName} AI Receptionist</h2>
          <p className="text-slate-400">Speaking with {config.userName}</p>
          <p className="text-slate-500 font-mono text-sm mt-2">{formatTime(duration)}</p>
        </div>

        <div className="relative w-full max-w-[400px] aspect-square flex items-center justify-center mb-8">
          <div className="absolute inset-0 bg-indigo-500/5 blur-3xl rounded-full"></div>
          <Visualizer isActive={true} volume={volume} />
        </div>

        <div className="flex gap-6">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onEndCall}
            className="group flex items-center gap-3 px-8 py-4 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-full transition-all border-2 border-red-500/20 hover:border-red-500"
          >
            <div className="p-1 bg-current rounded-full">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-inherit group-hover:text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="font-semibold">End Call</span>
          </motion.button>
        </div>

        <div className="mt-8 p-4 bg-slate-800/30 rounded-lg border border-slate-700 max-w-lg text-center">
          <p className="text-sm text-slate-400">
            <span className="text-indigo-400 font-semibold">Tip:</span> Try asking "Do you have any openings tomorrow afternoon?" or "What are your prices?"
          </p>
        </div>
      </div>

      {/* Right Side: Inline Calendar */}
      <div className="w-full lg:w-1/2 h-[600px] min-h-[600px] bg-slate-800/50 rounded-2xl overflow-hidden border border-slate-700/50 shadow-2xl relative">
        <Cal
          namespace="30min"
          calLink="tedca-corp-qt97mx/30min"
          style={{ width: "100%", height: "100%", overflow: "scroll" }}
          config={{ layout: "month_view" }}
        />
      </div>
    </motion.div>
  );
};
