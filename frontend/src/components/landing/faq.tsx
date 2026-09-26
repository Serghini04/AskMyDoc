"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Plus } from "lucide-react";
import { Badge } from "./badge";

const faqs = [
  {
    q: "How does AskMyDoc answer my questions?",
    a: "Your document is split into chunks and embedded into a vector index. When you ask something, the most relevant chunks are retrieved and handed to the language model, which answers strictly from that context — and tells you when the answer isn't in your docs.",
  },
  {
    q: "What file types are supported?",
    a: "PDF and plain text today. Each file is validated and size-checked before upload, then processed in the background — you'll see its status update from processing to ready.",
  },
  {
    q: "Is my data shared across chats?",
    a: "No. Documents are scoped to the chat session you upload them to. Deleting a chat removes its messages, documents, and indexed vectors.",
  },
  {
    q: "Does it make things up?",
    a: "The assistant is instructed to rely only on the retrieved passages from your documents. If the context doesn't contain the answer, it says so rather than inventing one.",
  },
  {
    q: "Do I need an account?",
    a: "No. Open the app, start a chat, and upload a file. It's built as a portfolio-grade RAG project — straightforward to run locally against the FastAPI backend.",
  },
];

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="relative border-t border-border-subtle">
      <div className="mx-auto max-w-3xl px-6 py-24">
        <div className="text-center">
          <Badge dot={false}>FAQ</Badge>
          <h2 className="font-display mt-6 text-4xl text-foreground md:text-5xl">
            Questions, answered.
          </h2>
        </div>

        <div className="mt-12 divide-y divide-border-subtle border-y border-border-subtle">
          {faqs.map((item, i) => {
            const isOpen = open === i;
            return (
              <div key={item.q}>
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between gap-4 py-5 text-left"
                >
                  <span className="text-base font-medium text-foreground">
                    {item.q}
                  </span>
                  <Plus
                    className={`h-4 w-4 shrink-0 text-muted transition-transform duration-200 ${
                      isOpen ? "rotate-45" : ""
                    }`}
                  />
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                      className="overflow-hidden"
                    >
                      <p className="pb-5 pr-8 text-sm leading-relaxed text-muted">
                        {item.a}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
