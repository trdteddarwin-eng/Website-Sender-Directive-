import { GoogleGenAI, LiveServerMessage, Modality } from '@google/genai';
import { createPcmBlob, decodeAudioData, base64ToUint8Array } from '../utils/audio-utils';
import { BusinessConfig, TranscriptItem } from '../types';
import { SYSTEM_INSTRUCTION_TEMPLATE } from '../constants';

export type ConnectionQuality = 'good' | 'fair' | 'poor';

export class GeminiLiveService {
  private ai: GoogleGenAI;
  private inputAudioContext: AudioContext | null = null;
  private outputAudioContext: AudioContext | null = null;
  private inputSource: MediaStreamAudioSourceNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private outputGainNode: GainNode | null = null;
  private analyzer: AnalyserNode | null = null;
  private nextStartTime: number = 0;
  private audioSources: Set<AudioBufferSourceNode> = new Set();
  private isConnected: boolean = false;
  private sessionPromise: Promise<any> | null = null;
  private processingId: number = 0;

  // Transcription State
  private currentInputText: string = '';
  private currentOutputText: string = '';
  private transcript: TranscriptItem[] = [];

  // Session management
  private sessionTimer: ReturnType<typeof setTimeout> | null = null;
  private warningTimer: ReturnType<typeof setTimeout> | null = null;
  private connectStartTime: number = 0;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 2;
  private lastConfig: BusinessConfig | null = null;
  private lastMediaStream: MediaStream | null = null;

  // Connection quality tracking
  private lastAudioChunkTime: number = 0;
  private audioGapCounts: number[] = []; // timestamps of large gaps
  private currentQuality: ConnectionQuality = 'good';

  // Session limits (ms)
  private static readonly SESSION_MAX_MS = 5 * 60 * 1000; // 5 min
  private static readonly SESSION_WARNING_MS = 4 * 60 * 1000; // 4 min

  // Callbacks
  public onVolumeChange: ((volume: number) => void) | null = null;
  public onDisconnect: (() => void) | null = null;
  public onTranscript: ((transcript: TranscriptItem[]) => void) | null = null;
  public onTimeout: ((info: { warning: boolean; disconnected: boolean }) => void) | null = null;
  public onReconnecting: ((attempt: number) => void) | null = null;
  public onReconnectFailed: (() => void) | null = null;
  public onConnectionQuality: ((quality: ConnectionQuality) => void) | null = null;

  constructor() {
    const apiKey = process.env.API_KEY;
    if (!apiKey) {
      console.error('API Key not found');
    }
    this.ai = new GoogleGenAI({ apiKey: apiKey || '', apiVersion: 'v1alpha' });
  }

  async connect(config: BusinessConfig) {
    if (this.isConnected) return;

    this.lastConfig = config;
    this.transcript = [];
    this.currentInputText = '';
    this.currentOutputText = '';
    this.processingId = 0;
    this.reconnectAttempts = 0;
    this.audioGapCounts = [];
    this.currentQuality = 'good';
    this.lastAudioChunkTime = 0;

    await this.establishConnection(config);
  }

  private async establishConnection(config: BusinessConfig) {
    try {
      // Initialize Audio Contexts
      this.inputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      this.outputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });

      // Output setup
      this.outputGainNode = this.outputAudioContext.createGain();
      this.analyzer = this.outputAudioContext.createAnalyser();
      this.analyzer.fftSize = 256;
      this.outputGainNode.connect(this.analyzer);
      this.analyzer.connect(this.outputAudioContext.destination);

      // Input setup (Microphone)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
        }
      });
      this.lastMediaStream = stream;

      // Start Analysis Loop
      this.startAnalysisLoop();

      // Connect to Gemini Live
      this.sessionPromise = this.ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-12-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } },
          },
          systemInstruction: SYSTEM_INSTRUCTION_TEMPLATE(config),
          inputAudioTranscription: {},
          outputAudioTranscription: {},
        },
        callbacks: {
          onopen: () => {
            console.log('Gemini Live Connection Opened');
            this.setupInputProcessing(stream);
            this.startSessionTimers();
          },
          onmessage: this.handleMessage.bind(this),
          onclose: () => {
            console.log('Gemini Live Connection Closed');
            this.handleConnectionLoss();
          },
          onerror: (e) => {
            console.error('Gemini Live Error', e);
            this.handleConnectionLoss();
          }
        }
      });

      this.isConnected = true;
      this.connectStartTime = Date.now();
    } catch (error) {
      console.error('Failed to connect:', error);
      this.cleanup();
      throw error;
    }
  }

  private startSessionTimers() {
    this.clearSessionTimers();

    // 4-min warning
    this.warningTimer = setTimeout(() => {
      if (this.onTimeout) {
        this.onTimeout({ warning: true, disconnected: false });
      }
    }, GeminiLiveService.SESSION_WARNING_MS);

    // 5-min hard cutoff
    this.sessionTimer = setTimeout(() => {
      if (this.onTimeout) {
        this.onTimeout({ warning: false, disconnected: true });
      }
      this.disconnect();
    }, GeminiLiveService.SESSION_MAX_MS);
  }

  private clearSessionTimers() {
    if (this.warningTimer) {
      clearTimeout(this.warningTimer);
      this.warningTimer = null;
    }
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer);
      this.sessionTimer = null;
    }
  }

  private async handleConnectionLoss() {
    if (!this.isConnected) return;

    this.cleanupAudio();

    if (this.reconnectAttempts < this.maxReconnectAttempts && this.lastConfig) {
      this.reconnectAttempts++;
      if (this.onReconnecting) {
        this.onReconnecting(this.reconnectAttempts);
      }

      await new Promise(resolve => setTimeout(resolve, 2000));

      try {
        await this.establishConnection(this.lastConfig);
      } catch (e) {
        console.error('Reconnect attempt failed:', e);
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          if (this.onReconnectFailed) {
            this.onReconnectFailed();
          }
          this.cleanup();
        } else {
          this.handleConnectionLoss();
        }
      }
    } else {
      if (this.reconnectAttempts >= this.maxReconnectAttempts && this.onReconnectFailed) {
        this.onReconnectFailed();
      }
      this.cleanup();
    }
  }

  getConnectionQuality(): ConnectionQuality {
    return this.currentQuality;
  }

  getSessionDuration(): number {
    if (!this.connectStartTime) return 0;
    return Math.floor((Date.now() - this.connectStartTime) / 1000);
  }

  private updateConnectionQuality() {
    const now = Date.now();
    // Keep only gaps from the last 30 seconds
    const recentGaps = this.audioGapCounts.filter(t => now - t < 30000);
    this.audioGapCounts = recentGaps;

    let newQuality: ConnectionQuality;
    if (recentGaps.length >= 5) {
      newQuality = 'poor';
    } else if (recentGaps.length >= 2) {
      newQuality = 'fair';
    } else {
      newQuality = 'good';
    }

    if (newQuality !== this.currentQuality) {
      this.currentQuality = newQuality;
      if (this.onConnectionQuality) {
        this.onConnectionQuality(newQuality);
      }
    }
  }

  async sendText(text: string) {
    if (!this.sessionPromise) return;

    this.transcript.push({ role: 'user', text, timestamp: new Date() });
    if (this.onTranscript) {
      this.onTranscript([...this.transcript]);
    }

    const session = await this.sessionPromise;
    await session.send({ parts: [{ text }] }, true);
  }

  private setupInputProcessing(stream: MediaStream) {
    if (!this.inputAudioContext) return;

    this.inputSource = this.inputAudioContext.createMediaStreamSource(stream);
    this.scriptProcessor = this.inputAudioContext.createScriptProcessor(2048, 1, 1);

    this.scriptProcessor.onaudioprocess = (e) => {
      if (!this.isConnected || !this.sessionPromise) return;

      const inputData = e.inputBuffer.getChannelData(0);
      const pcmBlob = createPcmBlob(inputData);

      this.sessionPromise.then((session) => {
        session.sendRealtimeInput({ audio: pcmBlob });
      });
    };

    this.inputSource.connect(this.scriptProcessor);

    const muteGain = this.inputAudioContext.createGain();
    muteGain.gain.value = 0;
    this.scriptProcessor.connect(muteGain);
    muteGain.connect(this.inputAudioContext.destination);
  }

  private async handleMessage(message: LiveServerMessage) {
    const serverContent = message.serverContent;

    // Handle Transcription
    if (serverContent?.inputTranscription) {
      this.currentInputText += serverContent.inputTranscription.text;
    }
    if (serverContent?.outputTranscription) {
      this.currentOutputText += serverContent.outputTranscription.text;
    }

    if (serverContent?.turnComplete) {
      this.commitTranscript();
    }

    if (serverContent?.interrupted) {
      console.log('User Interrupted!');
      this.processingId++;
      this.commitTranscript();
      this.stopAllAudio();
      return;
    }

    const base64Audio = serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;

    if (base64Audio) {
      // Track audio gaps for connection quality
      const now = Date.now();
      if (this.lastAudioChunkTime > 0) {
        const gap = now - this.lastAudioChunkTime;
        if (gap > 2000) {
          this.audioGapCounts.push(now);
          this.updateConnectionQuality();
        }
      }
      this.lastAudioChunkTime = now;

      if (!this.outputAudioContext || !this.outputGainNode) {
        console.warn('Audio received but output context/gain not ready');
        return;
      }

      if (this.outputAudioContext.state === 'suspended') {
        console.log('Resuming suspended output audio context');
        await this.outputAudioContext.resume();
      }

      try {
        const currentId = this.processingId;
        const uint8Array = base64ToUint8Array(base64Audio);
        console.log(`Received audio chunk: ${uint8Array.byteLength} bytes`);

        const audioBuffer = await decodeAudioData(uint8Array, this.outputAudioContext);
        console.log(`Decoded audio: ${audioBuffer.duration}s`);

        if (currentId !== this.processingId) {
          console.log('Discarding audio chunk due to interruption');
          return;
        }

        const source = this.outputAudioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.outputGainNode);

        const ctxNow = this.outputAudioContext.currentTime;
        if (this.nextStartTime < ctxNow) {
          this.nextStartTime = ctxNow;
        }

        console.log(`Scheduling audio at ${this.nextStartTime} (current: ${ctxNow})`);
        source.start(this.nextStartTime);
        this.nextStartTime += audioBuffer.duration;

        this.audioSources.add(source);
        source.onended = () => {
          this.audioSources.delete(source);
        };
      } catch (e) {
        console.error('Error decoding audio chunk', e);
      }
    }
  }

  private commitTranscript() {
    let changed = false;
    if (this.currentInputText.trim()) {
      this.transcript.push({ role: 'user', text: this.currentInputText.trim(), timestamp: new Date() });
      this.currentInputText = '';
      changed = true;
    }
    if (this.currentOutputText.trim()) {
      this.transcript.push({ role: 'model', text: this.currentOutputText.trim(), timestamp: new Date() });
      this.currentOutputText = '';
      changed = true;
    }

    if (changed && this.onTranscript) {
      this.onTranscript([...this.transcript]);
    }
  }

  private stopAllAudio() {
    this.audioSources.forEach(source => {
      try {
        source.stop();
      } catch (e) { }
    });
    this.audioSources.clear();

    if (this.outputAudioContext) {
      this.nextStartTime = this.outputAudioContext.currentTime;
    }
  }

  private startAnalysisLoop() {
    const updateVolume = () => {
      if (!this.isConnected) return;

      if (this.analyzer) {
        const dataArray = new Uint8Array(this.analyzer.frequencyBinCount);
        this.analyzer.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const average = sum / dataArray.length;
        const vol = Math.min(1, average / 128);

        if (this.onVolumeChange) {
          this.onVolumeChange(vol);
        }
      }
      requestAnimationFrame(updateVolume);
    };
    updateVolume();
  }

  async disconnect() {
    this.isConnected = false;
    this.cleanup();
  }

  private cleanupAudio() {
    this.stopAllAudio();

    if (this.inputSource) this.inputSource.disconnect();
    if (this.scriptProcessor) this.scriptProcessor.disconnect();
    if (this.outputGainNode) this.outputGainNode.disconnect();
    if (this.analyzer) this.analyzer.disconnect();

    if (this.inputAudioContext) this.inputAudioContext.close();
    if (this.outputAudioContext) this.outputAudioContext.close();

    this.inputSource = null;
    this.scriptProcessor = null;
    this.outputGainNode = null;
    this.analyzer = null;
    this.inputAudioContext = null;
    this.outputAudioContext = null;
  }

  private cleanup() {
    this.isConnected = false;
    this.clearSessionTimers();
    this.cleanupAudio();
    this.sessionPromise = null;

    if (this.lastMediaStream) {
      this.lastMediaStream.getTracks().forEach(t => t.stop());
      this.lastMediaStream = null;
    }

    if (this.onDisconnect) this.onDisconnect();
  }
}
