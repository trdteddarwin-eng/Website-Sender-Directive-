import React, { useEffect, useState, useRef } from 'react';
import { TranscriptItem, BusinessConfig } from '../types';
import { WEBHOOK_URL } from '../constants';

interface TranscriptSummaryProps {
  transcript: TranscriptItem[];
  config: BusinessConfig;
  onClose: () => void;
}

export const TranscriptSummary: React.FC<TranscriptSummaryProps> = ({ transcript, config, onClose }) => {
  const [webhookStatus, setWebhookStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  const hasAttemptedSend = useRef(false);

  useEffect(() => {
    if (WEBHOOK_URL && transcript.length > 0 && !hasAttemptedSend.current) {
      sendWebhook();
    }
  }, [transcript]);

  const sendWebhook = async () => {
    if (!WEBHOOK_URL) return;

    hasAttemptedSend.current = true;
    setWebhookStatus('sending');

    try {
      const payload = {
        type: 'TRANSCRIPT_SUMMARY',
        timestamp: new Date().toISOString(),
        businessName: config.businessName,
        customerName: config.userName || `${config.firstName} ${config.lastName}`,
        phone: config.phone,
        email: config.email,
        industry: config.industry,
        services: config.services,
        avgTicketValue: config.avgTicketValue,
        transcript: transcript.map(item => `${item.role === 'user' ? 'Customer' : 'AI'}: ${item.text}`).join('\n'),
        summary: "Conversation from AI Receptionist Demo"
      };

      const response = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setWebhookStatus('success');
      } else {
        console.error("Webhook failed with status:", response.status);
        setWebhookStatus('error');
      }
    } catch (error) {
      console.error("Webhook error:", error);
      setWebhookStatus('error');
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto animate-fade-in p-4 z-50">
      <div className="bg-offwhite border border-dark rounded-none shadow-[8px_8px_0px_#111111] flex flex-col max-h-[80vh] relative">
        <div className="hiw-noise opacity-30 pointer-events-none absolute inset-0 z-0"></div>

        {/* Header */}
        <div className="p-6 border-b border-dark bg-paper flex items-center justify-between relative z-10">
          <div>
            <h2 className="font-heading text-2xl font-bold tracking-tighter uppercase text-dark">Call Transcript</h2>
            <p className="font-mono text-[10px] text-dark/60 uppercase tracking-widest mt-1">Summary of conversation with {config.firstName} {config.lastName}</p>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-paper hover:bg-signal text-dark hover:text-paper border border-dark rounded-none font-mono text-[10px] uppercase tracking-widest transition-colors shadow-[2px_2px_0px_#111111] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
          >
            Close Transcript
          </button>
        </div>

        {/* Webhook Status Bar */}
        {WEBHOOK_URL && (
          <div className={`px-6 py-2 font-mono text-[10px] uppercase tracking-widest flex items-center justify-between border-b border-dark/20 relative z-10 ${webhookStatus === 'success' ? 'bg-signal/10 text-signal' :
            webhookStatus === 'error' ? 'bg-red-50 text-red-600' :
              'bg-dark/5 text-dark/70'
            }`}>
            <div className="flex items-center gap-2">
              {webhookStatus === 'sending' && <div className="w-2 h-2 bg-current rounded-none animate-pulse"></div>}
              {webhookStatus === 'success' && <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
              {webhookStatus === 'error' && <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>}

              <span>
                {webhookStatus === 'idle' && "Ready to sync..."}
                {webhookStatus === 'sending' && "Syncing conversation data..."}
                {webhookStatus === 'success' && "Conversation data successfully synced"}
                {webhookStatus === 'error' && "Failed to sync data"}
              </span>
            </div>
            {webhookStatus === 'error' && (
              <button onClick={() => sendWebhook()} className="underline hover:text-signal">Retry</button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10">
          {transcript.length === 0 ? (
            <div className="text-center py-12 text-dark/40 font-mono text-xs uppercase tracking-widest">
              <p>No conversation recorded.</p>
            </div>
          ) : (
            transcript.map((item, index) => (
              <div
                key={index}
                className={`flex ${item.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-none px-5 py-4 border ${item.role === 'user'
                    ? 'bg-dark text-paper border-dark shadow-[4px_4px_0px_#E63B2E]'
                    : 'bg-paper text-dark border-dark/20 shadow-[2px_2px_0px_#111111]'
                    }`}
                >
                  <div className="font-mono text-[9px] text-current/50 uppercase tracking-widest mb-2 font-bold">
                    {item.role === 'user' ? 'Customer' : 'AI Receptionist'}
                  </div>
                  <p className="font-sans text-sm leading-relaxed">{item.text}</p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer / Call to action */}
        <div className="p-6 bg-offwhite border-t border-dark relative z-10">
          <div className="flex items-start gap-4 p-4 bg-signal/5 border border-signal rounded-none shadow-[2px_2px_0px_#E63B2E]">
            <div className="p-2 bg-signal border border-dark rounded-none">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-paper" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <h3 className="font-mono text-[10px] font-bold text-signal uppercase tracking-widest">Revenue Opportunity</h3>
              <p className="font-sans text-sm text-dark/80 mt-1">
                This transcript demonstrates how the AI captured information automatically.
                Missed calls like this cost {config.businessName} an estimated <span className="font-mono text-signal bg-signal/10 px-1 font-bold">${config.avgTicketValue}</span> per occurrence.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};