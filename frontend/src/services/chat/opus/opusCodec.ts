import { CHANNELS, FRAME_SIZE, OPUS_APPLICATION, SAMPLE_RATE } from "./constants";
import { waitForOpusModule } from "./loadOpus";

type OpusModule = Awaited<ReturnType<typeof waitForOpusModule>>;

export interface OpusEncoderHandle {
  encode: (pcmData: Int16Array) => Uint8Array | null;
  destroy: () => void;
}

export interface OpusDecoderHandle {
  decode: (opusData: Uint8Array) => Int16Array | null;
  destroy: () => void;
}

export async function createOpusEncoder(): Promise<OpusEncoderHandle> {
  const mod = await waitForOpusModule();
  const encoderPtr = mod._malloc(mod._opus_encoder_get_size(CHANNELS));
  const err = mod._opus_encoder_init(encoderPtr, SAMPLE_RATE, CHANNELS, OPUS_APPLICATION);
  if (err < 0) {
    mod._free(encoderPtr);
    throw new Error(`Opus 编码器初始化失败: ${err}`);
  }

  return {
    encode(pcmData: Int16Array) {
      if (pcmData.length !== FRAME_SIZE) {
        return null;
      }
      const pcmPtr = mod._malloc(pcmData.length * 2);
      for (let i = 0; i < pcmData.length; i++) {
        mod.HEAP16[(pcmPtr >> 1) + i] = pcmData[i];
      }
      const maxEncodedSize = 4000;
      const encodedPtr = mod._malloc(maxEncodedSize);
      const encodedBytes = mod._opus_encode(encoderPtr, pcmPtr, FRAME_SIZE, encodedPtr, maxEncodedSize);
      mod._free(pcmPtr);
      if (encodedBytes < 0) {
        mod._free(encodedPtr);
        return null;
      }
      const encodedData = new Uint8Array(encodedBytes);
      for (let i = 0; i < encodedBytes; i++) {
        encodedData[i] = mod.HEAPU8[encodedPtr + i];
      }
      mod._free(encodedPtr);
      return encodedData;
    },
    destroy() {
      mod._free(encoderPtr);
    },
  };
}

export async function createOpusDecoder(): Promise<OpusDecoderHandle> {
  const mod = await waitForOpusModule();
  const decoderPtr = mod._malloc(mod._opus_decoder_get_size(CHANNELS));
  const err = mod._opus_decoder_init(decoderPtr, SAMPLE_RATE, CHANNELS);
  if (err < 0) {
    mod._free(decoderPtr);
    throw new Error(`Opus 解码器初始化失败: ${err}`);
  }

  return {
    decode(opusData: Uint8Array) {
      const opusPtr = mod._malloc(opusData.length);
      mod.HEAPU8.set(opusData, opusPtr);
      const pcmPtr = mod._malloc(FRAME_SIZE * 2);
      const decodedSamples = mod._opus_decode(decoderPtr, opusPtr, opusData.length, pcmPtr, FRAME_SIZE, 0);
      mod._free(opusPtr);
      if (decodedSamples < 0) {
        mod._free(pcmPtr);
        return null;
      }
      const decodedData = new Int16Array(decodedSamples);
      for (let i = 0; i < decodedSamples; i++) {
        decodedData[i] = mod.HEAP16[(pcmPtr >> 1) + i];
      }
      mod._free(pcmPtr);
      return decodedData;
    },
    destroy() {
      mod._free(decoderPtr);
    },
  };
}

export type { OpusModule };
