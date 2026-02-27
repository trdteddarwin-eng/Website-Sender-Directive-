import { BusinessConfig, TranscriptItem } from '../types';
import { signPayload } from '../utils/hmac';
import { API_BASE_URL } from '../constants';

const WEBHOOK_SECRET = import.meta.env.VITE_WEBHOOK_SECRET || '';

async function signedFetch(url: string, body: object): Promise<Response> {
  const bodyStr = JSON.stringify(body);
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const signature = WEBHOOK_SECRET
    ? await signPayload(timestamp + '.' + bodyStr, WEBHOOK_SECRET)
    : '';

  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Signature': signature,
      'X-Timestamp': timestamp,
    },
    body: bodyStr,
  });
}

export async function submitLead(config: BusinessConfig): Promise<Response> {
  return signedFetch(`${API_BASE_URL}/api/voice-demo/lead`, {
    first_name: config.firstName,
    last_name: config.lastName,
    email: config.email,
    phone: config.phone || '',
    business_name: config.businessName || '',
    industry: config.industry || '',
    services: config.services || '',
    avg_ticket_value: config.avgTicketValue || '',
  });
}

export async function submitTranscript(
  config: BusinessConfig,
  transcript: TranscriptItem[],
  callDuration: number
): Promise<Response> {
  return signedFetch(`${API_BASE_URL}/api/voice-demo/transcript`, {
    email: config.email,
    call_duration: callDuration,
    transcript: transcript.map(item =>
      `${item.role === 'user' ? 'Customer' : 'AI'}: ${item.text}`
    ).join('\n'),
  });
}

export async function testWebhook(): Promise<Response> {
  return signedFetch(`${API_BASE_URL}/api/voice-demo/test`, {
    type: 'TEST_EVENT',
    timestamp: new Date().toISOString(),
    summary: 'Test event from setup screen.',
  });
}
