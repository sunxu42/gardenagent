export function AssistantThinkingIndicator() {
  return (
    <span className="ios-thinking" role="status" aria-label="正在思考">
      <span className="ios-thinking__dots" aria-hidden="true">
        <span className="ios-thinking__dot" />
        <span className="ios-thinking__dot" />
        <span className="ios-thinking__dot" />
      </span>
    </span>
  );
}
