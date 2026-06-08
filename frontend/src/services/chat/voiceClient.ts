import { CHANNELS, FRAME_SIZE, SAMPLE_RATE, SCRIPT_PROCESSOR_BUFFER } from "./opus/constants";
import { convertFloat32ToInt16 } from "./opus/audioUtils";
import { OpusAudioPlayer } from "./opus/audioPlayback";
import { createOpusDecoder, createOpusEncoder } from "./opus/opusCodec";

export interface VoiceClientCallbacks {
  onSendOpus: (opusData: Uint8Array) => void;
  onPlaybackStart?: () => void;
  onPlaybackIdle?: () => void;
}

export interface VoiceClient {
  start: (callbacks: VoiceClientCallbacks) => Promise<void>;
  stop: () => Promise<void>;
  handleIncomingOpus: (opusData: Uint8Array) => void;
  interruptPlayback: () => void;
}

export function createVoiceClient(): VoiceClient {
  let mediaStream: MediaStream | null = null;
  let audioContext: AudioContext | null = null;
  let mediaSource: MediaStreamAudioSourceNode | null = null;
  let processor: ScriptProcessorNode | null = null;
  let encoder: Awaited<ReturnType<typeof createOpusEncoder>> | null = null;
  let decoder: Awaited<ReturnType<typeof createOpusDecoder>> | null = null;
  let player: OpusAudioPlayer | null = null;
  let pcmRemainder = new Int16Array(0);
  let sendOpus: ((opusData: Uint8Array) => void) | null = null;
  let active = false;

  const processPcmChunk = (float32Data: Float32Array) => {
    if (!active || !encoder || !sendOpus) {
      return;
    }
    const int16Data = convertFloat32ToInt16(float32Data);
    const combined = new Int16Array(pcmRemainder.length + int16Data.length);
    combined.set(pcmRemainder);
    combined.set(int16Data, pcmRemainder.length);

    const frameCount = Math.floor(combined.length / FRAME_SIZE);
    for (let i = 0; i < frameCount; i++) {
      const frame = combined.subarray(i * FRAME_SIZE, (i + 1) * FRAME_SIZE);
      const encoded = encoder.encode(frame);
      if (encoded) {
        sendOpus(encoded);
      }
    }

    const remaining = combined.length % FRAME_SIZE;
    pcmRemainder = remaining > 0 ? combined.subarray(frameCount * FRAME_SIZE) : new Int16Array(0);
  };

  const flushRemainder = () => {
    if (!active || !encoder || !sendOpus || pcmRemainder.length === 0) {
      pcmRemainder = new Int16Array(0);
      return;
    }
    const padded = new Int16Array(FRAME_SIZE);
    padded.set(pcmRemainder);
    const encoded = encoder.encode(padded);
    if (encoded) {
      sendOpus(encoded);
    }
    pcmRemainder = new Int16Array(0);
  };

  return {
    async start(callbacks) {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("无法使用麦克风，请使用 HTTPS 或 localhost。");
      }

      sendOpus = callbacks.onSendOpus;
      encoder = await createOpusEncoder();
      decoder = await createOpusDecoder();
      audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
      if (audioContext.state === "suspended") {
        await audioContext.resume();
      }

      player = new OpusAudioPlayer(audioContext, decoder, {
        onPlaybackStart: callbacks.onPlaybackStart,
        onPlaybackIdle: callbacks.onPlaybackIdle,
      });

      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: SAMPLE_RATE,
          channelCount: CHANNELS,
        },
      });

      mediaSource = audioContext.createMediaStreamSource(mediaStream);
      processor = audioContext.createScriptProcessor(SCRIPT_PROCESSOR_BUFFER, CHANNELS, CHANNELS);
      processor.onaudioprocess = (event) => {
        processPcmChunk(event.inputBuffer.getChannelData(0));
      };

      // ScriptProcessor 需接到输出图才会触发；增益为 0 避免麦克风回放到扬声器干扰 TTS
      const monitorGain = audioContext.createGain();
      monitorGain.gain.value = 0;
      mediaSource.connect(processor);
      processor.connect(monitorGain);
      monitorGain.connect(audioContext.destination);
      active = true;
      pcmRemainder = new Int16Array(0);
    },

    async stop() {
      active = false;
      flushRemainder();
      sendOpus?.(new Uint8Array(0));

      processor?.disconnect();
      mediaSource?.disconnect();
      processor = null;
      mediaSource = null;

      mediaStream?.getTracks().forEach((track) => track.stop());
      mediaStream = null;

      player?.stop();
      player = null;

      encoder?.destroy();
      decoder?.destroy();
      encoder = null;
      decoder = null;
      sendOpus = null;

      if (audioContext) {
        await audioContext.close().catch(() => undefined);
        audioContext = null;
      }
    },

    handleIncomingOpus(opusData) {
      if (!player) {
        return;
      }
      void player.enqueue(opusData);
    },

    interruptPlayback() {
      player?.stop();
    },
  };
}
