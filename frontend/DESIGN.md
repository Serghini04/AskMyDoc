# AskMyDoc — Design Notes

The goal was a frontend that reads as **intentionally crafted**, not assembled from a
component-library default. The direction is a *monochrome, near-black studio* aesthetic
inspired by high-end product sites (reference: firassa.studio): a cool near-black canvas,
white ink, white as the single "accent", heavy tight display type, and bordered dark cards
on a faint blueprint grid.

## Tokens

All design decisions live as CSS custom properties in [`src/app/globals.css`](src/app/globals.css)
and are exposed to Tailwind via `@theme inline`. Nothing is hard-coded in components.

### Color
A single **cool neutral ramp** (`--ink-900` → `--paper`) carries the whole UI, so surfaces
relate to each other instead of being arbitrary grays. The palette is **monochrome**:
**white is the accent** (`--accent #fafafa`) — primary actions are white-on-black, exactly
like the reference. Borders are translucent white (`rgba(255,255,255,0.06–0.09)`) for that
crisp dark-card edge. Two supporting hues (`--success` green, `--danger`) are reserved
strictly for status dots and destructive actions.

Semantic aliases (`--background`, `--surface`, `--border`, `--foreground`, `--muted`,
`--faint`) sit on top of the ramp so components speak in roles, not raw shades.

### Typography
- **Display:** Geist at weight **800** with tight negative tracking (`.font-display`) — a
  heavy grotesque used large for headlines and the wordmark, matching the bold, confident
  feel of the reference.
- **Text:** Geist Sans for body and UI.
- **Mono:** Geist Mono for code.

A deliberate scale (4xl–[5.25rem] for display, sm–lg for text) keeps hierarchy obvious.

### Texture & motion (the "creative" layer)
- `.bg-grid` — a faint blueprint grid, radially masked, behind the hero and closing CTA.
- `.card-surface` — a subtle top-lit gradient over `--surface` for dark cards with depth.
- `.grain` — an SVG film-grain overlay (`feTurbulence`, ~4% opacity, `overlay` blend) for
  premium texture over flat darks.
- **Aurora backdrop** (`AuroraBackground`) — two slowly drifting, blurred color blobs
  (cool blue + violet + white) on the dark canvas, pure CSS keyframes.
- **Floating product shot** — the hero mockup gently floats (`float-soft`) above a slowly
  rotating conic glow ring (`spin-slow`).
- **Scroll reveals** (`Reveal`) — sections fade-and-rise into view once, with small
  per-item stagger on grids.
- **Button micro-interactions** — primary lifts with a soft white glow on hover.
- Pill components everywhere (nav, badges, buttons are `rounded-full`).

All animation is decorative and collapses to ~0ms under `prefers-reduced-motion`
(handled by the global reset in `globals.css`).

### Space, radius, motion
- Spacing follows Tailwind's 4px rhythm; sections breathe with large vertical padding.
- Three radii (`sm`, `md`, `lg`) used consistently.
- Motion is **subtle and fast** (150–250ms, custom ease `[0.22, 1, 0.36, 1]`): entrance
  fades on the hero, slide-over for the mobile drawer, scale-in for dialogs. All of it is
  disabled under `prefers-reduced-motion`.

## Anti-"AI-template" choices
- No purple gradient hero, no row of three identical emoji cards.
- The shadcn default theme is **not** used; the one primitive (`Button`) is hand-styled
  against our tokens.
- Real typographic contrast (serif display vs. clean sans), asymmetric/left-aligned section
  intros, and a restrained palette instead of centered-everything.

## Accessibility
- Visible, on-brand focus ring (`:focus-visible`) everywhere.
- Dialogs use `role="alertdialog"`, trap initial focus, and close on Escape.
- Icon-only controls carry `aria-label`s; status icons are labelled.
- Color contrast targets WCAG AA on the dark canvas.
