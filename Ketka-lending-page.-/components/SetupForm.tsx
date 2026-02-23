import React, { useState } from 'react';
import { BusinessConfig, AppState } from '../types';
import { DEFAULT_SERVICES, WEBHOOK_URL } from '../constants';
import { motion } from 'framer-motion';

interface SetupFormProps {
  onComplete: (config: BusinessConfig) => void;
  isLoading: boolean;
}

export const SetupForm: React.FC<SetupFormProps> = ({ onComplete, isLoading }) => {
  const [config, setConfig] = useState<BusinessConfig>({
    firstName: '',
    lastName: '',
    phone: '',
    email: '',
    businessName: '',
    industry: '',
    services: DEFAULT_SERVICES,
    avgTicketValue: '150'
  });
  const [testStatus, setTestStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (config.firstName && config.businessName && config.industry) {
      // Send initial lead data to webhook
      if (WEBHOOK_URL) {
        try {
          await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: 'LEAD_SUBMISSION',
              timestamp: new Date().toISOString(),
              businessName: config.businessName,
              customerName: `${config.firstName} ${config.lastName}`.trim(),
              phone: config.phone,
              email: config.email,
              industry: config.industry,
              avgTicketValue: config.avgTicketValue,
              services: config.services,
              summary: "New lead submitted from demo setup form."
            })
          });
        } catch (error) {
          console.error("Failed to send lead webhook:", error);
          // Continue anyway
        }
      }
      onComplete(config);
    }
  };

  const handleTestWebhook = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!WEBHOOK_URL) return;

    setTestStatus('sending');
    try {
      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'TEST_EVENT',
          timestamp: new Date().toISOString(),
          businessName: config.businessName || "Test Business",
          customerName: `${config.firstName} ${config.lastName}`.trim() || "Test User",
          phone: config.phone,
          email: config.email,
          avgTicketValue: config.avgTicketValue,
          transcript: "Customer: This is a test message to verify the integration.\nAI: Connection successful.",
          summary: "This is a test event generated from the setup screen."
        })
      });

      if (response.ok) {
        setTestStatus('success');
        setTimeout(() => setTestStatus('idle'), 3000);
      } else {
        setTestStatus('error');
        setTimeout(() => setTestStatus('idle'), 3000);
      }
    } catch (error) {
      console.error(error);
      setTestStatus('error');
      setTimeout(() => setTestStatus('idle'), 3000);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-md mx-auto p-6 md:p-8 bg-offwhite border border-dark shadow-[4px_4px_0px_#111111] relative"
    >
      <div className="hiw-noise opacity-30 pointer-events-none absolute inset-0 z-0"></div>

      <motion.div variants={itemVariants} className="text-center mb-8 relative z-10">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-signal border border-dark mb-4 group-hover:scale-105 transition-transform">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-paper" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </div>
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-dark mb-2 tracking-tighter uppercase">Try the AI Receptionist</h1>
        <p className="font-mono text-[10px] text-dark/50 uppercase tracking-widest">Fill in your info for a personalized demo.</p>
      </motion.div>

      <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
        <div className="grid grid-cols-2 gap-3">
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">First Name</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="Alex"
              value={config.firstName}
              onChange={(e) => setConfig({ ...config, firstName: e.target.value })}
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Last Name</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="Smith"
              value={config.lastName}
              onChange={(e) => setConfig({ ...config, lastName: e.target.value })}
            />
          </motion.div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Phone</label>
            <input
              type="tel"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="+1 555 000 0000"
              value={config.phone}
              onChange={(e) => setConfig({ ...config, phone: e.target.value })}
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Email</label>
            <input
              type="email"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="alex@example.com"
              value={config.email}
              onChange={(e) => setConfig({ ...config, email: e.target.value })}
            />
          </motion.div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Business Name</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="Elite Dental"
              value={config.businessName}
              onChange={(e) => setConfig({ ...config, businessName: e.target.value })}
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Industry</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="Dentistry"
              value={config.industry}
              onChange={(e) => setConfig({ ...config, industry: e.target.value })}
            />
          </motion.div>
        </div>

        <motion.div variants={itemVariants}>
          <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Avg. Customer Value ($)</label>
          <div className="relative">
            <span className="absolute left-4 top-3 text-dark/50 font-mono">$</span>
            <input
              type="number"
              required
              className="w-full pl-8 pr-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="150"
              value={config.avgTicketValue}
              onChange={(e) => setConfig({ ...config, avgTicketValue: e.target.value })}
            />
          </div>
          <p className="text-xs text-dark/40 mt-2 font-sans">Used to calculate potential lost revenue.</p>
        </motion.div>

        <motion.div variants={itemVariants}>
          <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Key Services (Comma separated)</label>
          <textarea
            className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm min-h-[80px]"
            value={config.services}
            onChange={(e) => setConfig({ ...config, services: e.target.value })}
          />
        </motion.div>

        <motion.div variants={itemVariants} className="pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-4 border font-mono font-bold uppercase tracking-widest text-xs transition-transform hover:scale-[1.02] shadow-sm flex items-center justify-center ${isLoading
              ? 'bg-dark/10 border-dark/20 text-dark/40 cursor-not-allowed'
              : 'bg-signal border-dark text-paper hover:bg-signal/90'
              }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-3">
                <span className="w-1.5 h-1.5 bg-paper rounded-full animate-ping"></span>
                Connecting...
              </span>
            ) : (
              "Start Live Demo"
            )}
          </button>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={handleTestWebhook}
              disabled={testStatus === 'sending'}
              className={`font-mono text-[10px] uppercase tracking-widest transition-colors ${testStatus === 'success' ? 'text-signal font-bold' :
                testStatus === 'error' ? 'text-red-600' :
                  'text-dark/40 hover:text-dark'
                }`}
            >
              {testStatus === 'idle' && "Test Webhook Connection"}
              {testStatus === 'sending' && "Sending Test Event..."}
              {testStatus === 'success' && "Test Event Sent Successfully!"}
              {testStatus === 'error' && "Connection Failed (Check Console)"}
            </button>
          </div>
        </motion.div>
      </form>
    </motion.div>
  );
};