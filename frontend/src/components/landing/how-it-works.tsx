import { Badge } from "./badge";
import { Reveal } from "@/components/util/reveal";

const steps = [
  {
    n: "01",
    title: "Upload",
    body: "Drop in a PDF or text file. It's chunked, embedded locally, and indexed in a vector store — scoped to this chat.",
  },
  {
    n: "02",
    title: "Ask",
    body: "Ask in plain language. The most relevant passages are retrieved from your document, not the open web.",
  },
  {
    n: "03",
    title: "Cite",
    body: "Answers are built strictly from the retrieved context — with the source spelled out, or an honest 'not in the docs'.",
  },
];

export function HowItWorks() {
  return (
    <section
      id="workflow"
      className="relative border-t border-border-subtle"
    >
      <div className="mx-auto max-w-6xl px-6 py-24">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge dot={false}>The workflow</Badge>
          <h2 className="font-display mt-6 text-4xl text-foreground md:text-5xl">
            From a pile of pages to a sourced answer.
          </h2>
          <p className="mt-4 text-muted">
            One flow, no tagging, no scrubbing page by page.
          </p>
        </Reveal>

        {/* Before / After */}
        <div className="mt-16 grid gap-5 md:grid-cols-2">
          <Reveal>
            <Panel
              label="Before"
              muted
              lines={["w-3/4", "w-1/2", "w-2/3", "w-1/3"]}
              caption="40 pages. Ctrl+F that doesn't understand synonyms. You skim, you guess, you miss things."
            />
          </Reveal>
          <Reveal delay={0.1}>
            <Panel
              label="AskMyDoc"
              lines={["w-full", "w-5/6", "w-full"]}
              caption="Ask retrieves the exact passages. The answer arrives with its source attached. One window, one flow."
            />
          </Reveal>
        </div>

        {/* Steps */}
        <div className="mt-20 grid gap-px overflow-hidden rounded-[var(--radius-lg)] border border-border-subtle bg-border-subtle md:grid-cols-3">
          {steps.map((step, i) => (
            <Reveal key={step.n} delay={i * 0.08} className="card-surface p-8">
              <span className="font-display text-2xl text-foreground">
                {step.n}
              </span>
              <h3 className="mt-5 text-lg font-semibold">{step.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted">
                {step.body}
              </p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function Panel({
  label,
  lines,
  caption,
  muted = false,
}: {
  label: string;
  lines: string[];
  caption: string;
  muted?: boolean;
}) {
  return (
    <div className="card-surface flex flex-col rounded-[var(--radius-lg)] border border-border p-6">
      <span
        className={`inline-flex w-fit rounded-full border px-2.5 py-1 text-xs ${
          muted
            ? "border-border-subtle text-faint"
            : "border-border bg-accent-soft text-foreground"
        }`}
      >
        {label}
      </span>

      <div className="mt-6 flex-1 space-y-2.5 rounded-lg border border-border-subtle bg-background/60 p-5">
        {lines.map((w, i) => (
          <div
            key={i}
            className={`h-2.5 rounded-full ${w} ${
              muted ? "bg-[var(--ink-700)]" : "bg-[var(--ink-500)]"
            }`}
          />
        ))}
      </div>

      <p className="mt-5 text-sm leading-relaxed text-muted">{caption}</p>
    </div>
  );
}
