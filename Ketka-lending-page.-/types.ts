export interface BusinessConfig {
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  businessName: string;
  industry: string;
  services?: string;
  avgTicketValue?: string;
  userName?: string;
}

export enum AppState {
  IDLE = 'IDLE',
  SETUP = 'SETUP',
  CONNECTING = 'CONNECTING',
  ACTIVE = 'ACTIVE',
  SUMMARY = 'SUMMARY',
  ERROR = 'ERROR'
}

export interface AudioVisualizerState {
  volume: number; // 0.0 to 1.0
}

export interface TranscriptItem {
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
}