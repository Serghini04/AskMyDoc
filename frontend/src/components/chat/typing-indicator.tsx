/** Three blinking dots shown in the assistant slot while a reply is generating. */
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5" aria-label="Assistant is typing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-muted"
          style={{ animation: "blink 1.4s infinite", animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  );
}
