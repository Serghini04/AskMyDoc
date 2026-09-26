import { FileText, Search, ShieldCheck, MessagesSquare } from "lucide-react";
import { Badge } from "./badge";
import { Reveal } from "@/components/util/reveal";

const features = [
  {
    icon: Search,
    title: "Semantic retrieval",
    body: "Questions are matched on meaning, not keywords, using local sentence embeddings — so paraphrases still find the right passage.",
  },
  {
    icon: ShieldCheck,
    title: "Grounded, not guessing",
    body: "Answers are constrained to the retrieved context. No outside knowledge leaks in, and gaps are admitted honestly.",
  },
  {
    icon: FileText,
    title: "PDF & text, per session",
    body: "Attach multiple documents to a conversation. Each chat keeps its own library, isolated from the rest.",
  },
  {
    icon: MessagesSquare,
    title: "Conversations that persist",
    body: "Every chat is saved with its history and sources, auto-named from your first question, ready to resume anytime.",
  },
];

export function Features() {
  return (
    <section id="features" className="relative border-t border-border-subtle">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge dot={false}>Under the hood</Badge>
          <h2 className="font-display mt-6 text-4xl text-foreground md:text-5xl">
            Built to be trusted.
          </h2>
          <p className="mt-4 text-muted">
            Answers you can act on — because you can check them.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2">
          {features.map(({ icon: Icon, title, body }, i) => (
            <Reveal
              key={title}
              delay={i * 0.08}
              className="card-surface group rounded-[var(--radius-lg)] border border-border p-7 transition-colors hover:border-[rgba(255,255,255,0.18)]"
            >
              <div className="grid h-11 w-11 place-items-center rounded-[var(--radius-md)] border border-border bg-background text-foreground transition-transform duration-300 group-hover:-translate-y-0.5">
                <Icon className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <h3 className="mt-6 text-lg font-semibold">{title}</h3>
              <p className="mt-2.5 text-sm leading-relaxed text-muted">{body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
