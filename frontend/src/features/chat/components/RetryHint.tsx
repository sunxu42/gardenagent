interface RetryHintProps {
  visible: boolean;
}

export function RetryHint({ visible }: RetryHintProps) {
  if (!visible) {
    return null;
  }

  return <span className="chat-ios-retry">发送失败可重试</span>;
}
