"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { Badge } from "./badge";
import { ProductPreview } from "./product-preview";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ease = [0.22, 1, 0.36, 1] as const;

function fadeUp(delay: number) {
  return {
    initial: { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6, ease, delay },
  };
}

export function Hero() {
  return (
    <section className="relative overflow-hidden">

      <div className="relative z-10 mx-auto max-w-5xl px-6 pb-12 pt-20 text-center md:pt-28">
        <motion.div {...fadeUp(0)}>
          <Badge>Grounded answers from your own documents</Badge>
        </motion.div>

        <motion.h1
          {...fadeUp(0.06)}
          className="font-display mx-auto mt-7 max-w-4xl text-5xl text-foreground sm:text-6xl md:text-[5.25rem]"
        >
          From scattered docs
          <br />
          to answers you can cite.
        </motion.h1>

        <motion.p
          {...fadeUp(0.12)}
          className="mx-auto mt-7 max-w-xl text-lg leading-relaxed text-muted"
        >
          Upload a PDF or note and chat with it. AskMyDoc reads only what you
          give it — retrieving the exact passages and answering with sources, not
          guesses.
        </motion.p>

        <motion.div
          {...fadeUp(0.18)}
          className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link
            href="/chat"
            className={cn(buttonVariants({ variant: "primary", size: "lg" }), "group")}
          >
            Launch AskMyDoc
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#workflow"
            className={buttonVariants({ variant: "secondary", size: "lg" })}
          >
            <Play className="h-3.5 w-3.5" />
            See how it works
          </a>
        </motion.div>

        <motion.p {...fadeUp(0.24)} className="mt-4 text-xs text-faint">
          No account. No setup. PDF &amp; text supported.
        </motion.p>
      </div>

      {/* Product shot with a soft glow ring behind it */}
      <motion.div
        initial={{ opacity: 0, y: 48 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.85, ease, delay: 0.3 }}
        className="relative z-10 mx-auto max-w-5xl px-6 pb-10"
      >
        <div
          aria-hidden
          className="spin-slow pointer-events-none absolute left-1/2 top-1/2 h-[120%] w-[120%] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-25 blur-3xl"
          style={{
            background:
              "conic-gradient(from 0deg, transparent, rgba(138,180,255,0.35), transparent 30%, rgba(196,163,255,0.3), transparent 60%, rgba(255,255,255,0.25), transparent)",
          }}
        />
        <div className="float-soft relative">
          <ProductPreview />
        </div>
      </motion.div>
    </section>
  );
}
