/**
 * Page-wide ambient backdrop for the landing page. Fixed to the viewport so the
 * same colored light sits behind every section as you scroll — no flat-black
 * gaps between sections. Pure CSS (gradients + grain), decorative, no JS.
 *
 * Rendered once at the top of the page; sections are transparent so this shows
 * through. Sits at z-0; page content is z-10.
 */
export function LandingBackground() {
  return (
    <div aria-hidden className="grain pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* Base multi-point color wash across the whole viewport */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(60% 50% at 12% 0%, rgba(99,102,241,0.30), transparent 60%),
            radial-gradient(55% 45% at 88% 8%, rgba(45,212,191,0.22), transparent 60%),
            radial-gradient(50% 50% at 50% 42%, rgba(168,85,247,0.16), transparent 60%),
            radial-gradient(55% 45% at 10% 88%, rgba(236,72,153,0.18), transparent 60%),
            radial-gradient(60% 50% at 92% 95%, rgba(99,102,241,0.22), transparent 62%)
          `,
        }}
      />

      {/* Faint blueprint grid over the whole page */}
      <div className="absolute inset-0 bg-grid opacity-60 [mask-image:radial-gradient(140%_100%_at_50%_0%,black,transparent_85%)]" />

      {/* A couple of slowly drifting accents for life */}
      <div
        className="aurora-a absolute left-[6%] top-[20%] h-[28rem] w-[28rem] rounded-full opacity-25 blur-[130px]"
        style={{ background: "radial-gradient(circle, #6366f1 0%, transparent 70%)" }}
      />
      <div
        className="aurora-b absolute right-[4%] top-[55%] h-[26rem] w-[26rem] rounded-full opacity-20 blur-[130px]"
        style={{ background: "radial-gradient(circle, #2dd4bf 0%, transparent 70%)" }}
      />
    </div>
  );
}
