import React, { useState } from 'react';
import { BusinessConfig } from '../types';
import { API_BASE_URL } from '../constants';
import { submitLead, testWebhook } from '../services/webhookService';
import { motion } from 'framer-motion';

interface SetupFormProps {
  onComplete: (config: BusinessConfig) => void;
  isLoading: boolean;
}

export const SetupForm: React.FC<SetupFormProps> = ({ onComplete, isLoading }) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [testStatus, setTestStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (firstName && lastName && email) {
      const config: BusinessConfig = {
        firstName,
        lastName,
        email,
      };

      if (API_BASE_URL) {
        try {
          await submitLead(config);
        } catch (error) {
          console.error('Failed to send lead webhook:', error);
        }
      }
      onComplete(config);
    }
  };

  const handleTestWebhook = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!API_BASE_URL) return;

    setTestStatus('sending');
    try {
      const response = await testWebhook();
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
        <p className="font-mono text-[10px] text-dark/50 uppercase tracking-widest">Talk to our AI receptionist live. See what it can do.</p>
      </motion.div>

      <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">First Name</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="Alex"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Last Name</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
              placeholder="Smith"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </motion.div>
        </div>

        <motion.div variants={itemVariants}>
          <label className="block font-mono text-[10px] font-bold text-dark/70 uppercase tracking-widest mb-1.5">Email</label>
          <input
            type="email"
            required
            className="w-full px-4 py-3 bg-paper border border-dark/20 rounded-none focus:border-dark focus:ring-1 focus:ring-dark text-dark placeholder-dark/30 transition-all outline-none font-sans text-sm"
            placeholder="alex@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
