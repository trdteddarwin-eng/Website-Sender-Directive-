import React, { useEffect, useState, useRef } from 'react';
import { BusinessConfig, TranscriptItem } from '../types';
import { Visualizer } from './Visualizer';
import { GeminiLiveService } from '../services/geminiLive';
import { APPOINTMENT_TRIGGER_PHRASES } from '../constants';
import { motion, AnimatePresence } from 'framer-motion';

interface ActiveCallProps {
  config: BusinessConfig;
  onEndCall: () => void;
  service: GeminiLiveService;
  transcript?: TranscriptItem[];
  isReconnecting?: boolean;
  reconnectAttempt?: number;
}

export const ActiveCall: React.FC<ActiveCallProps> = ({
  config,
  onEndCall,
  service,
  transcript = [],
  isReconnecting = false,
  reconnectAttempt = 0,
}) => {
  const [volume, setVolume] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showEndConfirm, setShowEndConfirm] = useState(false);
  const [transcriptExpanded, setTranscriptExpanded] = useState(false);
  const [showAppointmentBooked, setShowAppointmentBooked] = useState(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const bookedTriggeredRef = useRef(false);

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

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcript]);

  // Auto-expand transcript on desktop when first message arrives
  useEffect(() => {
    if (transcript.length === 1 && window.innerWidth >= 768) {
      setTranscriptExpanded(true);
    }
  }, [transcript.length]);

  // Detect appointment booking from AI responses
  useEffect(() => {
    if (bookedTriggeredRef.current) return;

    const lastModelMsg = [...transcript].reverse().find(t => t.role === 'model');
    if (!lastModelMsg) return;

    const text = lastModelMsg.text.toLowerCase();
    const triggered = APPOINTMENT_TRIGGER_PHRASES.some(phrase => text.includes(phrase));

    if (triggered) {
      bookedTriggeredRef.current = true;
      setShowAppointmentBooked(true);
      setTimeout(() => setShowAppointmentBooked(false), 4000);
    }
  }, [transcript]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleEndClick = () => {
    setShowEndConfirm(true);
  };

  const confirmEnd = () => {
    setShowEndConfirm(false);
    onEndCall();
  };

  const cancelEnd = () => {
    setShowEndConfirm(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center justify-center w-full h-full px-4 py-6 relative"
    >
      {/* Reconnecting Overlay */}
      <AnimatePresence>
        {isReconnecting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-30 bg-paper/90 flex flex-col items-center justify-center gap-4"
          >
            <div className="w-3 h-3 bg-signal animate-ping"></div>
            <p className="font-mono text-xs text-dark/70 uppercase tracking-widest">
              Reconnecting... (Attempt {reconnectAttempt})
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* End Call Confirmation Overlay */}
      <AnimatePresence>
        {showEndConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-30 bg-dark/80 flex flex-col items-center justify-center gap-6"
          >
            <p className="font-heading text-2xl font-bold text-paper uppercase tracking-tighter">
              End this call?
            </p>
            <div className="flex gap-4">
              <button
                onClick={confirmEnd}
                className="px-8 py-3 bg-signal border border-paper text-paper font-mono text-xs font-bold uppercase tracking-widest hover:bg-signal/80 transition-colors"
              >
                End Call
              </button>
              <button
                onClick={cancelEnd}
                className="px-8 py-3 bg-dark border border-paper/30 text-paper font-mono text-xs font-bold uppercase tracking-widest hover:bg-dark/80 transition-colors"
              >
                Continue
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Appointment Booked Animation */}
      <AnimatePresence>
        {showAppointmentBooked && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -20 }}
            transition={{ type: 'spring', damping: 15, stiffness: 200 }}
            className="absolute top-4 left-1/2 -translate-x-1/2 z-40 pointer-events-none"
          >
            <div className="bg-dark border-2 border-success px-6 py-4 shadow-[4px_4px_0px_#34C759] flex items-center gap-3">
              <div className="w-10 h-10 bg-success flex items-center justify-center shrink-0">
                <motion.svg
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-6 h-6 text-paper"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <motion.path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  />
                </motion.svg>
              </div>
              <div>
                <p className="font-heading text-lg font-bold text-paper uppercase tracking-tighter">
                  Appointment Booked
                </p>
                <p className="font-mono text-[10px] text-paper/60 uppercase tracking-widest">
                  AI handled it automatically
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Minimal Header */}
      <div className="text-center mb-8 relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 border border-signal bg-signal/10 text-signal font-mono text-[10px] font-bold uppercase tracking-widest mb-3">
          <span className="w-2 h-2 bg-signal animate-pulse"></span>
          LIVE DEMO
        </div>
        <p className="font-mono text-[10px] text-dark/50 uppercase tracking-widest">Bright Smile Dental</p>
      </div>

      {/* Compact Visualizer */}
      <div className="relative w-[140px] h-[140px] md:w-[200px] md:h-[200px] flex items-center justify-center mb-4">
        <Visualizer isActive={true} volume={volume} />
      </div>

      {/* Timer */}
      <p className="text-dark font-mono text-4xl md:text-5xl font-bold tracking-tighter mb-8 relative z-10">{formatTime(duration)}</p>

      {/* Speaking indicator */}
      <p className="font-mono text-[10px] text-dark/70 uppercase tracking-widest mb-8 relative z-10">Speaking with {config.firstName}</p>

      {/* End Call Button */}
      <button
        onClick={handleEndClick}
        className="w-16 h-16 md:w-20 md:h-20 bg-signal hover:bg-signal/90 border border-dark border-b-4 border-r-4 flex items-center justify-center transition-all active:border-b active:border-r active:translate-y-[3px] active:translate-x-[3px] group relative z-10"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 md:h-8 md:w-8 text-paper group-hover:scale-90 transition-transform" viewBox="0 0 20 20" fill="currentColor">
          <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
        </svg>
      </button>

      <p className="font-mono text-[10px] text-dark/40 uppercase tracking-widest mt-4 relative z-10">Tap to end call</p>

      {/* Live Transcript Panel */}
      <div className="mt-8 w-full max-w-lg relative z-10">
        {/* Toggle button (always visible, especially useful on mobile) */}
        <button
          onClick={() => setTranscriptExpanded(!transcriptExpanded)}
          className="w-full flex items-center justify-between px-4 py-2 bg-paper border border-dark/20 font-mono text-[10px] text-dark/60 uppercase tracking-widest hover:bg-offwhite transition-colors"
        >
          <span>Live Transcript ({transcript.length})</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className={`w-4 h-4 transition-transform ${transcriptExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <AnimatePresence>
          {transcriptExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="max-h-[200px] md:max-h-[300px] overflow-y-auto bg-offwhite border border-t-0 border-dark/20 p-4 space-y-3">
                {transcript.length === 0 ? (
                  <p className="text-center font-mono text-[10px] text-dark/30 uppercase tracking-widest py-4">
                    Waiting for conversation...
                  </p>
                ) : (
                  transcript.map((item, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <span
                        className={`shrink-0 px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-widest ${
                          item.role === 'user'
                            ? 'bg-dark text-paper'
                            : 'bg-signal text-paper'
                        }`}
                      >
                        {item.role === 'user' ? 'You' : 'AI'}
                      </span>
                      <p className="font-sans text-xs text-dark/80 leading-relaxed">{item.text}</p>
                    </div>
                  ))
                )}
                <div ref={transcriptEndRef} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Tip */}
      <div className="mt-6 px-4 py-3 bg-paper border border-dark border-l-4 border-l-signal max-w-xs text-center relative z-10 shadow-[2px_2px_0px_#111111]">
        <p className="font-mono text-[10px] text-dark/70 tracking-tight">
          Try: "I'd like to book a cleaning" or "What are your hours?"
        </p>
      </div>
    </motion.div>
  );
};
