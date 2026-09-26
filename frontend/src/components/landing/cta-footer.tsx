import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Badge } from "./badge";
import { Reveal } from "@/components/util/reveal";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const guarantees = ["PDF & text support", "Sources on every answer", "No account required"];

export function CtaFooter() {
  return (
    <footer className="relative border-t border-border-subtle">
      {/* Big closing CTA */}
      <div className="relative overflow-hidden border-b border-border-subtle">
        <Reveal className="relative z-10 mx-auto max-w-3xl px-6 py-28 text-center">
          <Badge>Open and ready</Badge>
          <h2 className="font-display mx-auto mt-7 max-w-2xl text-5xl text-foreground md:text-6xl">
            Put your documents to work.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-muted">
            Open a chat, upload your first file, and ask away. It takes about a
            minute.
          </p>

          <div className="mt-9 flex justify-center">
            <Link
              href="/chat"
              className={cn(
                buttonVariants({ variant: "primary", size: "lg" }),
                "group",
              )}
            >
              Launch AskMyDoc
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Link>
          </div>

          <ul className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-faint">
            {guarantees.map((g) => (
              <li key={g} className="inline-flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-success" />
                {g}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>

      {/* Footer bar */}
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-faint sm:flex-row">
        <Logo />
        <nav className="flex items-center gap-6">
          <a href="#workflow" className="transition-colors hover:text-foreground">
            Workflow
          </a>
          <a href="#features" className="transition-colors hover:text-foreground">
            Features
          </a>
          <a href="#faq" className="transition-colors hover:text-foreground">
            FAQ
          </a>
        </nav>
        <p>© {new Date().getFullYear()} AskMyDoc. RAG portfolio project.</p>
      </div>
    </footer>
  );
}
