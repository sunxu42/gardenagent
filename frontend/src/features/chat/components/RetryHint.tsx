import { Badge } from "@/components/ui/badge";

interface RetryHintProps {
  visible: boolean;
}

export function RetryHint({ visible }: RetryHintProps) {
  if (!visible) {
    return null;
  }

  return <Badge variant="outline">发送失败可重试。</Badge>;
}
