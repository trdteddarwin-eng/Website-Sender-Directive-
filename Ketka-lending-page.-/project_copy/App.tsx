import React, { useState, useRef, useEffect } from 'react';
import { AppState, BusinessConfig, TranscriptItem } from './types';
import { GeminiLiveService } from './services/geminiLive';
import { SetupForm } from './components/SetupForm';
import { ActiveCall } from './components/ActiveCall';
import { TranscriptSummary } from './components/TranscriptSummary';
import { AnimatePresence, motion } from 'framer-motion';
import Cal, { getCalApi } from "@calcom/embed-react";

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>(AppState.SETUP);
  const [config, setConfig] = useState<BusinessConfig | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);

  // Use ref to keep the service singleton across renders
  const liveServiceRef = useRef<GeminiLiveService | null>(null);

  useEffect(() => {
    liveServiceRef.current = new GeminiLiveService();

    // Bind the transcript callback
    liveServiceRef.current.onTranscript = (newTranscript) => {
      setTranscript(newTranscript);
    };

    return () => {
      liveServiceRef.current?.disconnect();
    };
  }, []);

  const handleSetupComplete = async (newConfig: BusinessConfig) => {
    setConfig(newConfig);
    setAppState(AppState.CONNECTING);
    setErrorMsg(null);
    setTranscript([]); // Reset transcript for new call

    try {
      if (liveServiceRef.current) {
        await liveServiceRef.current.connect(newConfig);
        setAppState(AppState.ACTIVE);

        // Trigger the AI to speak first
        setTimeout(() => {
          liveServiceRef.current?.sendText("The user has connected. Please greet them now.");
        }, 100);
      }
    } catch (e) {
      console.error(e);
      setAppState(AppState.SETUP);
      setErrorMsg("Failed to access microphone or connect to AI service. Please check permissions and try again.");
    }
  };

  const handleEndCall = () => {
    if (liveServiceRef.current) {
      liveServiceRef.current.disconnect();
    }
    // Transition to Summary instead of Setup
    setAppState(AppState.SUMMARY);
  };

  const handleCloseSummary = () => {
    setAppState(AppState.SETUP);
    setConfig(null);
  };

  useEffect(() => {
    (async function () {
      const cal = await getCalApi({ "namespace": "30min" });
      cal("ui", { "styles": { "branding": { "brandColor": "#7d3131" } }, "hideEventTypeDetails": false, "layout": "month_view" });
    })();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-black text-slate-100 selection:bg-indigo-500/30 overflow-x-hidden">

      {/* Header */}
      <header className="p-6 flex items-center justify-between border-b border-slate-800/50 backdrop-blur-sm fixed top-0 w-full z-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
            </svg>
          </div>
          <span className="font-bold text-lg tracking-tight">Reception<span className="text-indigo-400">AI</span></span>
        </div>
        <div className="text-xs font-medium px-3 py-1 bg-slate-800 rounded-full text-slate-400 border border-slate-700">
          Powered by Gemini 2.5
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-4 flex flex-col items-center min-h-screen justify-center relative">

        {/* Background Animation */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-indigo-500/20 rounded-full blur-[120px]"
          />
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.2, 0.4, 0.2]
            }}
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 2
            }}
            className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] bg-violet-500/20 rounded-full blur-[100px]"
          />
        </div>

        <AnimatePresence mode="wait">
          {errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-8 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 max-w-md text-center text-sm z-10"
            >
              {errorMsg}
            </motion.div>
          )}

          {appState === AppState.SETUP && (
            <motion.div
              key="setup"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              className="w-full max-w-xl z-10"
            >
              <SetupForm onComplete={handleSetupComplete} isLoading={false} />
            </motion.div>
          )}

          {appState === AppState.CONNECTING && (
            <motion.div
              key="connecting"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              transition={{ duration: 0.5 }}
              className="w-full max-w-xl z-10"
            >
              <SetupForm onComplete={() => { }} isLoading={true} />
            </motion.div>
          )}

          {appState === AppState.ACTIVE && config && liveServiceRef.current && (
            <motion.div
              key="active"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.5 }}
              className="w-full z-10"
            >
              <ActiveCall
                config={config}
                service={liveServiceRef.current}
                onEndCall={handleEndCall}
              />
            </motion.div>
          )}

          {appState === AppState.SUMMARY && config && (
            <motion.div
              key="summary"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              transition={{ duration: 0.5 }}
              className="w-full z-10"
            >
              <TranscriptSummary
                transcript={transcript}
                config={config}
                onClose={handleCloseSummary}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Bottom Embed */}
        <div className="w-full max-w-4xl mt-12 z-10">
          <Cal
            namespace="30min"
            calLink="tedca-corp-qt97mx/30min"
            style={{ width: "100%", height: "100%", overflow: "scroll" }}
            config={{ layout: "month_view" }}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
