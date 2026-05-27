"""Self-contained interactive CSS for static HTML export (no JS)."""

CSS_INTERACTIVE = """
html { scroll-behavior: smooth; }
.card, .module-card, .team-card {
  transition: transform var(--alf-motion-duration, 0.25s) ease,
    box-shadow var(--alf-motion-duration, 0.25s) ease;
}
.card:hover, .module-card:hover, .team-card:hover {
  transform: var(--alf-card-transform, translateY(-4px));
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}
.theme-minimal .card:hover,
.theme-minimal .module-card:hover,
.theme-minimal .team-card:hover {
  transform: none;
  box-shadow: none;
}
.theme-corporate .card { box-shadow: 0 1px 3px rgba(15,23,42,0.06); }
.stack-tag {
  transition: background var(--alf-motion-duration, 0.2s) ease,
    border-color var(--alf-motion-duration, 0.2s) ease;
}
.stack-tag:hover { filter: brightness(1.05); }
.team-contrib details { margin-top: 0.5rem; font-size: 0.85rem; color: var(--alf-muted); }
.team-contrib summary { cursor: pointer; color: var(--alf-accent); font-weight: 500; }
.hero--gradient { background: var(--alf-hero-gradient) !important; }
.hero--cards { border-left: 6px solid var(--alf-accent); padding-left: 1.25rem; }
.hero--bold { background: var(--alf-hero-gradient) !important; }
.hero--future-3d {
  position: relative;
  isolation: isolate;
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
/* future 3D hook — WebGL/Three.js can mount on .hero--future-3d */
"""

ACCENT_HEX = {
    "blue": "#2563eb",
    "violet": "#7C3AED",
    "green": "#059669",
}

RADIUS_MAP = {"sharp": "4px", "soft": "8px", "rounded": "16px"}
GAP_MAP = {"compact": "1rem", "normal": "1.5rem", "spacious": "2rem"}
