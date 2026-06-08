import { CHANNELS, SAMPLE_RATE } from "./constants";
import { convertInt16ToFloat32 } from "./audioUtils";
import type { OpusDecoderHandle } from "./opusCodec";

const IDLE_DEBOUNCE_MS = 500;

export class OpusAudioPlayer {
  private audioContext: AudioContext;
  private decoder: OpusDecoderHandle;
  private bufferQueue: Uint8Array[] = [];
  private isBuffering = false;
  private isPlaying = false;
  private pcmQueue: number[] = [];
  private playingSource: AudioBufferSourceNode | null = null;
  private idleTimer: ReturnType<typeof setTimeout> | null = null;
  private playbackStarted = false;
  private onPlaybackStart?: () => void;
  private onPlaybackIdle?: () => void;

  constructor(
    audioContext: AudioContext,
    decoder: OpusDecoderHandle,
    callbacks?: { onPlaybackStart?: () => void; onPlaybackIdle?: () => void }
  ) {
    this.audioContext = audioContext;
    this.decoder = decoder;
    this.onPlaybackStart = callbacks?.onPlaybackStart;
    this.onPlaybackIdle = callbacks?.onPlaybackIdle;
  }

  enqueue(opusPacket: Uint8Array) {
    this.clearIdleTimer();

    if (opusPacket.length === 0) {
      this.scheduleIdleCheck();
      return;
    }

    this.bufferQueue.push(opusPacket);

    if (!this.isPlaying && !this.isBuffering) {
      this.startBuffering();
      return;
    }

    if (this.isPlaying && this.bufferQueue.length > 0) {
      this.drainBufferToPcm();
    }
  }

  stop() {
    this.clearIdleTimer();
    this.bufferQueue = [];
    this.pcmQueue = [];
    this.isBuffering = false;
    this.isPlaying = false;
    this.playbackStarted = false;
    if (this.playingSource) {
      try {
        this.playingSource.stop();
      } catch {
        // ignore if already stopped
      }
      this.playingSource = null;
    }
    this.onPlaybackIdle?.();
  }

  private clearIdleTimer() {
    if (this.idleTimer !== null) {
      clearTimeout(this.idleTimer);
      this.idleTimer = null;
    }
  }

  private scheduleIdleCheck() {
    this.clearIdleTimer();
    this.idleTimer = setTimeout(() => {
      this.idleTimer = null;
      if (this.bufferQueue.length > 0) {
        this.drainBufferToPcm();
        if (this.pcmQueue.length > 0 && !this.isPlaying) {
          void this.beginPlayback();
        }
        return;
      }
      if (!this.isPlaying && this.pcmQueue.length === 0) {
        this.playbackStarted = false;
        this.onPlaybackIdle?.();
      }
    }, IDLE_DEBOUNCE_MS);
  }

  private startBuffering() {
    if (this.isBuffering || this.isPlaying) {
      return;
    }
    this.isBuffering = true;
    window.setTimeout(() => {
      if (!this.isBuffering) {
        return;
      }
      this.isBuffering = false;
      if (this.bufferQueue.length === 0) {
        return;
      }
      this.drainBufferToPcm();
      if (this.pcmQueue.length > 0) {
        void this.beginPlayback();
      }
    }, 300);
  }

  private drainBufferToPcm() {
    while (this.bufferQueue.length > 0) {
      const frame = this.bufferQueue.shift();
      if (!frame) {
        continue;
      }
      const decoded = this.decoder.decode(frame);
      if (decoded && decoded.length > 0) {
        this.pcmQueue.push(...convertInt16ToFloat32(decoded));
      }
    }
  }

  private async ensureContextRunning() {
    if (this.audioContext.state === "suspended") {
      await this.audioContext.resume();
    }
  }

  private async beginPlayback() {
    if (this.isPlaying || this.pcmQueue.length === 0) {
      return;
    }
    await this.ensureContextRunning();
    this.isPlaying = true;
    if (!this.playbackStarted) {
      this.playbackStarted = true;
      this.onPlaybackStart?.();
    }
    this.playNextChunk();
  }

  private playNextChunk() {
    if (this.pcmQueue.length === 0) {
      if (this.bufferQueue.length > 0) {
        this.drainBufferToPcm();
      }
      if (this.pcmQueue.length > 0) {
        void this.beginPlayback();
        return;
      }
      this.isPlaying = false;
      this.scheduleIdleCheck();
      return;
    }

    const chunkSize = Math.min(this.pcmQueue.length, SAMPLE_RATE);
    const samples = this.pcmQueue.splice(0, chunkSize);
    const audioBuffer = this.audioContext.createBuffer(CHANNELS, samples.length, SAMPLE_RATE);
    audioBuffer.copyToChannel(new Float32Array(samples), 0);

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);
    this.playingSource = source;
    source.onended = () => {
      this.playingSource = null;
      if (this.bufferQueue.length > 0) {
        this.drainBufferToPcm();
      }
      this.playNextChunk();
    };
    source.start();
  }
}
