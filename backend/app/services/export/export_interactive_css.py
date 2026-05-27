"""Self-contained interactive CSS for static HTML export (no JS)."""

CSS_INTERACTIVE = """
html { scroll-behavior: smooth; }
section { scroll-margin-top: 4rem; }

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .card, .module-card, .team-card, .stack-tag,
  .section-nav a, .alf-section-nav a {
    transition: none !important;
  }
  .card:hover, .module-card:hover, .team-card:hover,
  .alf-card--interactive:hover {
    transform: none !important;
    box-shadow: none !important;
  }
  .hero--future-3d::before,
  .hero--future-3d::after {
    transform: none !important;
  }
}

.section-nav,
.alf-section-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
  padding: 0.75rem 0;
  margin-bottom: var(--alf-gap);
  border-bottom: 1px solid var(--alf-border);
  position: sticky;
  top: 0;
  z-index: 10;
  background: color-mix(in srgb, var(--alf-bg) 92%, transparent);
  backdrop-filter: blur(6px);
}
.section-nav a,
.alf-section-nav a {
  color: var(--alf-muted);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.35rem 0.65rem;
  border-radius: calc(var(--alf-radius) / 2);
  transition: color var(--alf-motion-duration, 0.25s) ease,
    background var(--alf-motion-duration, 0.25s) ease;
}
.section-nav a:hover,
.alf-section-nav a:hover,
.section-nav a:focus-visible,
.alf-section-nav a:focus-visible {
  color: var(--alf-accent);
  background: var(--alf-accent-light);
  outline: none;
}

.card,
.module-card,
.team-card,
.alf-card--interactive {
  transition: transform var(--alf-motion-duration, 0.25s) ease,
    box-shadow var(--alf-motion-duration, 0.25s) ease,
    border-color var(--alf-motion-duration, 0.25s) ease;
}
.card:hover,
.module-card:hover,
.team-card:hover,
.alf-card--interactive:hover {
  transform: var(--alf-card-transform, translateY(-4px));
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.theme-minimal .card:hover,
.theme-minimal .module-card:hover,
.theme-minimal .team-card:hover,
.theme-minimal .alf-card--interactive:hover {
  transform: none;
  box-shadow: none;
}
.theme-minimal .card,
.theme-minimal .module-card,
.theme-minimal .team-card,
.theme-minimal .alf-card--interactive {
  box-shadow: none;
  border-color: var(--alf-border);
}

.theme-corporate .card,
.theme-corporate .module-card,
.theme-corporate .team-card {
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.theme-tech .module-card,
.theme-tech .team-card,
.theme-tech .alf-card--interactive {
  background: color-mix(in srgb, var(--alf-surface) 85%, transparent);
  backdrop-filter: blur(8px);
  border-color: rgba(99, 102, 241, 0.35);
}
.theme-tech .module-card:hover,
.theme-tech .team-card:hover,
.theme-tech .alf-card--interactive:hover {
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.25);
}

.theme-bold .module-card,
.theme-bold .team-card,
.theme-bold .alf-card--interactive {
  border-left: 4px solid var(--alf-accent);
}
.theme-bold .module-card:hover,
.theme-bold .team-card:hover,
.theme-bold .alf-card--interactive:hover {
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12);
}

.stack-tag {
  transition: background var(--alf-motion-duration, 0.2s) ease,
    border-color var(--alf-motion-duration, 0.2s) ease,
    filter var(--alf-motion-duration, 0.2s) ease;
}
.stack-tag:hover { filter: brightness(1.05); }

.collapsible-section {
  margin-top: 0.5rem;
  border: 1px solid var(--alf-border);
  border-radius: var(--alf-radius);
  padding: 0.75rem 1rem;
  background: var(--alf-surface);
}
.collapsible-section summary {
  cursor: pointer;
  color: var(--alf-accent);
  font-weight: 500;
  font-size: 0.9rem;
  list-style: none;
}
.collapsible-section summary::-webkit-details-marker { display: none; }
.collapsible-section[open] summary { margin-bottom: 0.75rem; }

.team-contrib details {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--alf-muted);
}
.team-contrib summary {
  cursor: pointer;
  color: var(--alf-accent);
  font-weight: 500;
}

.hero--gradient { background: var(--alf-hero-gradient) !important; }
.hero--cards { border-left: 6px solid var(--alf-accent); padding-left: 1.25rem; }
.hero--bold { background: var(--alf-hero-gradient) !important; }
.hero--future-3d {
  position: relative;
  isolation: isolate;
  overflow: visible;
}
.hero--future-3d::before {
  content: "";
  position: absolute;
  inset: -8% -6% auto;
  height: 65%;
  background: var(--alf-hero-gradient);
  transform: perspective(800px) rotateX(8deg);
  opacity: 0.85;
  z-index: -1;
  border-radius: var(--alf-radius);
}
.hero--future-3d::after {
  content: "";
  position: absolute;
  inset: 12% 8% auto;
  height: 38%;
  background: radial-gradient(ellipse at center, var(--alf-accent-light), transparent 72%);
  transform: perspective(600px) rotateX(-4deg) translateZ(-20px);
  opacity: 0.45;
  z-index: -2;
  border-radius: var(--alf-radius);
  pointer-events: none;
}
/* future 3D hook — WebGL/Three.js can mount on .hero--future-3d */
"""

SECTION_NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("essence", "Суть"),
    ("tasks", "Задачи"),
    ("modules", "Системы"),
    ("stack", "Стек"),
    ("team", "Команда"),
    ("outlook", "Перспектива"),
)

LONG_TEXT_CHARS = 320
LONG_LIST_ITEMS = 6

ACCENT_HEX = {
    "blue": "#2563eb",
    "violet": "#7C3AED",
    "green": "#059669",
}

RADIUS_MAP = {"sharp": "4px", "soft": "8px", "rounded": "16px"}
GAP_MAP = {"compact": "1rem", "normal": "1.5rem", "spacious": "2rem"}
