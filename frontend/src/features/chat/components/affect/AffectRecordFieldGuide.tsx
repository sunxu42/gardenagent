import { Bot, Heart, MessageCircle, Users } from "lucide-react";
import { GuideModuleCard } from "./GuideSection";

/** 左侧记录栏字段说明 — 业务优先级仅次于本轮快照 */
export function AffectRecordFieldGuide() {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      <GuideModuleCard
        accent="violet"
        icon={<MessageCircle className="h-3.5 w-3.5" aria-hidden />}
        label="用户情绪"
        detail="从你的话解读本轮 V/A/D，每轮独立感知、无跨轮状态机。关系栏 trust/warmth 表示你对助手态度的累积变化。"
      />
      <GuideModuleCard
        accent="sky"
        icon={<Bot className="h-3.5 w-3.5" aria-hidden />}
        label="助手语气"
        detail="Agent 状态机中的 V/A/D。「相对上轮」为相对上轮结束状态的偏移（红升绿降）。"
      />
      <GuideModuleCard
        accent="amber"
        icon={<Heart className="h-3.5 w-3.5" aria-hidden />}
        label="回应态度"
        detail="共情方式 + 语气立场，决定助手怎么接你的话（安抚、庆祝、澄清等）。"
      />
      <GuideModuleCard
        accent="slate"
        icon={<Users className="h-3.5 w-3.5" aria-hidden />}
        label="关系"
        detail="信任与亲近缓慢累积，影响回应是否更敞开、直接。"
      />
    </div>
  );
}
