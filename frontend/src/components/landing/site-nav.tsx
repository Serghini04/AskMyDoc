import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { buttonVariants } from "@/components/ui/button";

/** Floating pill navigation, centered at the top of the landing page. */
export function SiteNav() {
  return (
    <header className="sticky top-0 z-40 px-4 pt-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-full border border-border bg-surface/70 py-2 pl-4 pr-2 backdrop-blur-xl">
        <div className="flex items-center gap-6">
          <Logo />
          <nav className="hidden items-center gap-5 text-sm text-muted md:flex">
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
        </div>

        <div className="flex items-center gap-2">
          <a
            href="#workflow"
            className="hidden px-3 text-sm text-muted transition-colors hover:text-foreground sm:block"
          >
            See it work
          </a>
          <Link
            href="/chat"
            className={buttonVariants({ variant: "primary", size: "sm" })}
          >
            Launch app
          </Link>
        </div>
      </div>
    </header>
  );
}
