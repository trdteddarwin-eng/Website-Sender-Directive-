export interface BusinessConfig {
  userName: string;
  businessName: string;
  industry: string;
  services: string;
  avgTicketValue: string;
}

export enum AppState {
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