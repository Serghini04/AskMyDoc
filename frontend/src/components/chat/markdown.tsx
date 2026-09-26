"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { CodeBlock } from "./code-block";

/**
 * Renders assistant answers as Markdown. Styling comes from the `.prose-answer`
 * rules in globals.css; here we only override the <pre> wrapper so code blocks
 * get a copy button, and force links to open safely.
 */
const components: Components = {
  pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
};

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose-answer">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
