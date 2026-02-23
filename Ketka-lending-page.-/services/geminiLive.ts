import { GoogleGenAI, LiveServerMessage, Modality } from '@google/genai';
import { createPcmBlob, decodeAudioData, base64ToUint8Array } from '../utils/audio-utils';
import { BusinessConfig, TranscriptItem } from '../types';
import { SYSTEM_INSTRUCTION_TEMPLATE } from '../constants';

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
  private currentInputText: string = "";
  private currentOutputText: string = "";
  private transcript: TranscriptItem[] = [];

  public onVolumeChange: ((volume: number) => void) | null = null;
  public onDisconnect: (() => void) | null = null;
  public onTranscript: ((transcript: TranscriptItem[]) => void) | null = null;

  constructor() {
    const apiKey = process.env.API_KEY;
    if (!apiKey) {
      console.error("API Key not found");
    }
    this.ai = new GoogleGenAI({ apiKey: apiKey || '' });
  }

  async connect(config: BusinessConfig) {
    if (this.isConnected) return;

    this.transcript = [];
    this.currentInputText = "";
    this.currentOutputText = "";
    this.processingId = 0;

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

      // Start Analysis Loop
      this.startAnalysisLoop();

      // Connect to Gemini Live
      this.sessionPromise = this.ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
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
          },
          onmessage: this.handleMessage.bind(this),
          onclose: () => {
            console.log('Gemini Live Connection Closed');
            this.cleanup();
          },
          onerror: (e) => {
            console.error('Gemini Live Error', e);
            this.cleanup();
          }
        }
      });

      this.isConnected = true;
    } catch (error) {
      console.error("Failed to connect:", error);
      this.cleanup();
      throw error;
    }
  }

  async sendText(text: string) {
    if (!this.sessionPromise) return;

    // Add to transcript immediately
    this.transcript.push({ role: 'user', text, timestamp: new Date() });
    if (this.onTranscript) {
      this.onTranscript([...this.transcript]);
    }

    const session = await this.sessionPromise;
    // content part with text
    await session.send({ parts: [{ text }] }, true);
  }

  private setupInputProcessing(stream: MediaStream) {
    if (!this.inputAudioContext) return;

    this.inputSource = this.inputAudioContext.createMediaStreamSource(stream);
    // Reduced buffer size to 2048 (approx 128ms) for better latency while maintaining stability
    this.scriptProcessor = this.inputAudioContext.createScriptProcessor(2048, 1, 1);

    this.scriptProcessor.onaudioprocess = (e) => {
      if (!this.isConnected || !this.sessionPromise) return;

      const inputData = e.inputBuffer.getChannelData(0);
      const pcmBlob = createPcmBlob(inputData);

      this.sessionPromise.then((session) => {
        session.sendRealtimeInput({ media: pcmBlob });
      });
    };

    this.inputSource.connect(this.scriptProcessor);

    // Mute input locally to prevent feedback, but keep the graph alive
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

    // Commit transcript on turn completion
    if (serverContent?.turnComplete) {
      this.commitTranscript();
    }

    // Handle Interruption immediately
    if (serverContent?.interrupted) {
      console.log("User Interrupted!");
      this.processingId++; // Invalidate any pending audio decoding
      this.commitTranscript(); // Commit whatever was said before interruption
      this.stopAllAudio();
      return; // Stop processing this message
    }

    const base64Audio = serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;

    if (base64Audio) {
      if (!this.outputAudioContext || !this.outputGainNode) {
        console.warn("Audio received but output context/gain not ready");
        return;
      }

      if (this.outputAudioContext.state === 'suspended') {
        console.log("Resuming suspended output audio context");
        await this.outputAudioContext.resume();
      }

      try {
        const currentId = this.processingId; // Capture ID at start of process
        const uint8Array = base64ToUint8Array(base64Audio);
        console.log(`Received audio chunk: ${uint8Array.byteLength} bytes`);

        const audioBuffer = await decodeAudioData(uint8Array, this.outputAudioContext);
        console.log(`Decoded audio: ${audioBuffer.duration}s`);

        // If an interruption occurred while we were awaiting decodeAudioData, 
        // processingId will have incremented. We should discard this audio chunk.
        if (currentId !== this.processingId) {
          console.log("Discarding audio chunk due to interruption");
          return;
        }

        const source = this.outputAudioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.outputGainNode);

        const now = this.outputAudioContext.currentTime;
        // Ensure gapless playback but handle drift
        if (this.nextStartTime < now) {
          this.nextStartTime = now;
        }

        console.log(`Scheduling audio at ${this.nextStartTime} (current: ${now})`);
        source.start(this.nextStartTime);
        this.nextStartTime += audioBuffer.duration;

        this.audioSources.add(source);
        source.onended = () => {
          this.audioSources.delete(source);
        };
      } catch (e) {
        console.error("Error decoding audio chunk", e);
      }
    }
  }

  private commitTranscript() {
    let changed = false;
    if (this.currentInputText.trim()) {
      this.transcript.push({ role: 'user', text: this.currentInputText.trim(), timestamp: new Date() });
      this.currentInputText = "";
      changed = true;
    }
    if (this.currentOutputText.trim()) {
      this.transcript.push({ role: 'model', text: this.currentOutputText.trim(), timestamp: new Date() });
      this.currentOutputText = "";
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
      } catch (e) { } // Ignore if already stopped
    });
    this.audioSources.clear();

    // Reset the playback cursor to current time to flush queue
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
        // Normalize to 0-1 range roughly
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

  private cleanup() {
    this.isConnected = false;
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
    this.sessionPromise = null;

    if (this.onDisconnect) this.onDisconnect();
  }
}