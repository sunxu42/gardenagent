"""Generate frontend/src/features/chat/ttsVoices.ts from Excel."""
import json
from pathlib import Path

import openpyxl

EXCEL = Path(r"c:\Users\sunxu\Desktop\新建 XLSX 工作表.xlsx")
OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "features" / "chat" / "ttsVoices.ts"
DEFAULT_VOICE = "zh_female_qingxinnvsheng_mars_bigtts"


def main() -> None:
    wb = openpyxl.load_workbook(EXCEL, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    items: list[dict] = []
    scene = ""
    for row in rows[1:]:
        cells = ["" if c is None else str(c).strip() for c in row]
        while len(cells) < 8:
            cells.append("")
        if cells[0]:
            scene = cells[0]
        label, value, lang = cells[1], cells[2], cells[3]
        if not value:
            continue
        emotions, tags, v2map, mix = cells[4], cells[5], cells[6], cells[7]
        desc_parts: list[str] = []
        if lang:
            desc_parts.append(f"语种/方言：{lang}")
        if emotions:
            desc_parts.append(f"支持情感：{emotions}")
        if tags:
            desc_parts.append(f"标签：{tags}")
        if v2map:
            desc_parts.append(f"对应2.0：{v2map}")
        if mix:
            desc_parts.append(f"MIX：{mix}")
        entry: dict = {
            "scene": scene or "未分类",
            "label": label or value,
            "value": value,
            "language": lang,
            "capabilities": emotions,
            "description": "；".join(desc_parts) if desc_parts else (label or value),
        }
        if tags:
            entry["tags"] = tags
        items.append(entry)

    vals = [x["value"] for x in items]
    default = DEFAULT_VOICE if DEFAULT_VOICE in vals else (vals[0] if vals else "")

    body = json.dumps(items, ensure_ascii=False, indent=2)
    text = f"""/**
 * 来源：新建 XLSX 工作表.xlsx（火山 1.0 音色清单）
 */

export interface TtsVoiceOption {{
  scene: string;
  label: string;
  value: string;
  language: string;
  capabilities: string;
  tags?: string;
  description: string;
}}

export const HUOSHAN_TTS_VOICE_OPTIONS: TtsVoiceOption[] = {body};

export const HUOSHAN_TTS_SUPPORTED_VOICES = HUOSHAN_TTS_VOICE_OPTIONS.map((item) => item.value);

export const HUOSHAN_TTS_VOICE_META: Record<string, {{ label?: string; description?: string }}> =
  Object.fromEntries(
    HUOSHAN_TTS_VOICE_OPTIONS.map((item) => [
      item.value,
      {{ label: item.label, description: item.description }},
    ])
  );

export const DEFAULT_TTS_VOICE = {json.dumps(default)};
"""
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {len(items)} voices to {OUT}, default={default}")


if __name__ == "__main__":
    main()
