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
    userName: '',
    businessName: '',
    industry: '',
    services: DEFAULT_SERVICES,
    avgTicketValue: '150'
  });
  const [testStatus, setTestStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (config.userName && config.businessName && config.industry) {
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
          customerName: config.userName || "Test User",
          avgTicketValue: config.avgTicketValue,
          transcript: [
            { role: 'user', text: 'This is a test message to verify the integration.', timestamp: new Date() },
            { role: 'model', text: 'Connection successful.', timestamp: new Date() }
          ],
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
      className="max-w-xl mx-auto p-8 bg-slate-800/50 rounded-2xl backdrop-blur-lg border border-slate-700 shadow-xl"
    >
      <motion.div variants={itemVariants} className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-full mb-4 shadow-lg shadow-indigo-500/30">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">Configure Your AI Receptionist</h1>
        <p className="text-slate-400">Customize the voice agent for the live demo.</p>
      </motion.div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <motion.div variants={itemVariants}>
          <label className="block text-sm font-medium text-slate-300 mb-2">Your First Name</label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-white placeholder-slate-500 transition-all"
            placeholder="e.g. Alex"
            value={config.userName}
            onChange={(e) => setConfig({ ...config, userName: e.target.value })}
          />
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div variants={itemVariants}>
            <label className="block text-sm font-medium text-slate-300 mb-2">Business Name</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-white placeholder-slate-500 transition-all"
              placeholder="e.g. Elite Dental"
              value={config.businessName}
              onChange={(e) => setConfig({ ...config, businessName: e.target.value })}
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <label className="block text-sm font-medium text-slate-300 mb-2">Industry</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-white placeholder-slate-500 transition-all"
              placeholder="e.g. Dentistry"
              value={config.industry}
              onChange={(e) => setConfig({ ...config, industry: e.target.value })}
            />
          </motion.div>
        </div>

        <motion.div variants={itemVariants}>
          <label className="block text-sm font-medium text-slate-300 mb-2">Avg. Customer Value ($)</label>
          <div className="relative">
            <span className="absolute left-4 top-3 text-slate-500">$</span>
            <input
              type="number"
              required
              className="w-full pl-8 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-white placeholder-slate-500 transition-all"
              placeholder="150"
              value={config.avgTicketValue}
              onChange={(e) => setConfig({ ...config, avgTicketValue: e.target.value })}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">Used to calculate potential lost revenue.</p>
        </motion.div>

        <motion.div variants={itemVariants}>
          <label className="block text-sm font-medium text-slate-300 mb-2">Key Services (Comma separated)</label>
          <textarea
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-white placeholder-slate-500 transition-all min-h-[80px]"
            value={config.services}
            onChange={(e) => setConfig({ ...config, services: e.target.value })}
          />
        </motion.div>

        <motion.div variants={itemVariants} className="pt-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isLoading}
            className={`w-full py-4 rounded-xl font-semibold text-lg transition-all shadow-lg ${isLoading
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-indigo-500/25'
              }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Connecting...
              </span>
            ) : (
              "Start Live Demo"
            )}
          </motion.button>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={handleTestWebhook}
              disabled={testStatus === 'sending'}
              className={`text-xs font-medium transition-colors ${testStatus === 'success' ? 'text-green-400' :
                  testStatus === 'error' ? 'text-red-400' :
                    'text-slate-500 hover:text-slate-300'
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