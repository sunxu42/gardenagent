type OpusModule = {
  _opus_encoder_get_size: (channels: number) => number;
  _opus_encoder_init: (encoder: number, rate: number, channels: number, application: number) => number;
  _opus_encode: (encoder: number, pcm: number, frameSize: number, data: number, maxDataBytes: number) => number;
  _opus_decoder_get_size: (channels: number) => number;
  _opus_decoder_init: (decoder: number, rate: number, channels: number) => number;
  _opus_decode: (
    decoder: number,
    data: number,
    len: number,
    pcm: number,
    frameSize: number,
    decodeFec: number
  ) => number;
  _malloc: (size: number) => number;
  _free: (ptr: number) => void;
  HEAPU8: Uint8Array;
  HEAP16: Int16Array;
};

function resolveOpusModule(): OpusModule | null {
  const win = window as Window & {
    Module?: OpusModule & { instance?: OpusModule };
    ModuleInstance?: OpusModule;
  };
  // libopus.js 导出为 Module.instance（与 web-portal 一致），不是 Module 包装函数本身
  const candidate = win.Module?.instance ?? win.ModuleInstance ?? win.Module;
  if (candidate && typeof candidate._opus_encoder_get_size === "function") {
    return candidate;
  }
  return null;
}

export function waitForOpusModule(timeoutMs = 8000): Promise<OpusModule> {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const tick = () => {
      const mod = resolveOpusModule();
      if (mod) {
        resolve(mod);
        return;
      }
      if (Date.now() - started > timeoutMs) {
        reject(new Error("Opus 库加载超时，请刷新页面重试。"));
        return;
      }
      window.setTimeout(tick, 50);
    };
    tick();
  });
}
