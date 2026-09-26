import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * Wordmark: a white rounded-square glyph + name. Text-based (no asset) so it
 * stays crisp and themeable. Used in the nav, chat header, and footer.
 */
export function Logo({
  className,
  href = "/",
}: {
  className?: string;
  href?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group inline-flex items-center gap-2.5 text-foreground",
        className,
      )}
    >
      <span
        aria-hidden
        className="grid h-7 w-7 place-items-center rounded-[7px] bg-accent text-[var(--ink-900)] font-display text-base leading-none transition-transform duration-300 group-hover:scale-95"
      >
        A
      </span>
      <span className="text-[0.95rem] font-semibold tracking-tight">
        AskMyDoc
      </span>
    </Link>
  );
}
