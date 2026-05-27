"""Per-preset self-contained CSS for static HTML export."""

CSS_MINIMAL = """
:root {
  --bg: #ffffff;
  --surface: #fafafa;
  --surface-2: #f5f5f5;
  --text: #1a1a1a;
  --muted: #737373;
  --accent: #525252;
  --accent-light: #f5f5f5;
  --border: #e5e5e5;
  --radius: 4px;
  --gap: 2.5rem;
  --font: "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.75; min-height: 100vh; }
.container { max-width: 960px; margin: 0 auto; padding: 3rem 2rem; }
.hero { padding: 4rem 0 3rem; border-bottom: 1px solid var(--border); margin-bottom: var(--gap); }
.hero h1 { font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 500; letter-spacing: -0.02em; }
.hero .tagline { color: var(--muted); margin-top: 1.5rem; max-width: 640px; font-size: 1rem; }
section { margin: var(--gap) 0; }
section h2 { font-size: 1.1rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); border: none; padding: 0; margin-bottom: 1.5rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; box-shadow: none; }
.card h3 { color: var(--text); font-weight: 500; font-size: 1rem; }
.grid-2, .grid-3 { gap: var(--gap); }
.stack-tag { background: var(--surface-2); color: var(--text); border-color: var(--border); }
footer { margin-top: 4rem; color: var(--muted); font-size: 0.8rem; text-align: center; border-top: 1px solid var(--border); padding-top: 2rem; }
"""

CSS_CORPORATE = """
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-2: #f1f5f9;
  --text: #0f172a;
  --muted: #64748b;
  --accent: #1e40af;
  --accent-light: #dbeafe;
  --border: #cbd5e1;
  --radius: 6px;
  --gap: 1.75rem;
  --font: "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; }
.container { max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }
.hero { padding: 2.5rem 0 2rem; border-bottom: 2px solid var(--accent-light); margin-bottom: var(--gap); background: var(--surface); border-radius: var(--radius); padding-left: 1.5rem; padding-right: 1.5rem; }
.hero h1 { font-size: clamp(1.85rem, 4vw, 2.75rem); font-weight: 600; color: var(--text); }
.hero .tagline { color: var(--muted); margin-top: 1rem; }
section h2 { font-size: 1.25rem; font-weight: 600; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; box-shadow: 0 1px 3px rgba(15,23,42,0.06); }
.card h3 { color: var(--text); font-weight: 600; }
.team-card .role { color: var(--accent); }
.stack-tag { background: var(--accent-light); color: var(--accent); border-color: var(--border); }
footer { margin-top: 3rem; border-top: 1px solid var(--border); padding-top: 1.5rem; color: var(--muted); text-align: center; font-size: 0.85rem; }
"""

CSS_TECH = """
:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --surface-2: #334155;
  --text: #f1f5f9;
  --muted: #94a3b8;
  --accent: #3b82f6;
  --accent-light: rgba(59,130,246,0.2);
  --border: rgba(148,163,184,0.25);
  --radius: 10px;
  --gap: 1.5rem;
  --font: "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
.hero { padding: 3rem 0 2rem; margin-bottom: var(--gap); border-bottom: 1px solid var(--border); background: linear-gradient(135deg, rgba(59,130,246,0.25) 0%, transparent 60%); border-radius: var(--radius); }
.hero h1 { font-size: clamp(2rem, 5vw, 3.25rem); font-weight: 700; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero .tagline { color: var(--muted); margin-top: 1rem; }
section h2 { font-size: 1.35rem; color: #93c5fd; border-bottom: 2px solid var(--accent-light); padding-bottom: 0.5rem; margin-bottom: 1rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; }
.card h3 { color: #93c5fd; }
.module-card { border-color: rgba(59,130,246,0.35); }
.stack-tag { background: var(--surface-2); color: #93c5fd; border-color: var(--border); }
footer { margin-top: 3rem; border-top: 1px solid var(--border); color: var(--muted); text-align: center; padding-top: 1.5rem; }
"""

CSS_BOLD = """
:root {
  --bg: #ffffff;
  --surface: #fff7ed;
  --surface-2: #ffedd5;
  --text: #1c1917;
  --muted: #78716c;
  --accent: #ea580c;
  --accent-light: #ffedd5;
  --border: #fed7aa;
  --radius: 12px;
  --gap: 1rem;
  --font: "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.5; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
.hero { padding: 2.5rem 0 1.5rem; margin-bottom: var(--gap); border-left: 6px solid var(--accent); padding-left: 1.25rem; }
.hero h1 { font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 800; line-height: 1.05; color: var(--text); }
.hero .tagline { font-size: 1.2rem; color: var(--muted); margin-top: 1rem; font-weight: 500; }
section { margin: 2rem 0; }
section h2 { font-size: clamp(1.5rem, 3vw, 2.25rem); font-weight: 800; color: var(--accent); border: none; margin-bottom: 1rem; }
.card { background: var(--surface); border: 2px solid var(--border); border-radius: var(--radius); padding: 1rem; transition: transform 0.35s ease, box-shadow 0.35s ease; }
.card h3 { font-size: 1.2rem; font-weight: 700; color: var(--text); }
.grid-2, .grid-3 { gap: var(--gap); }
.stack-tag { font-weight: 600; background: var(--accent-light); color: var(--accent); border: 2px solid var(--accent); }
footer { margin-top: 2.5rem; font-weight: 600; color: var(--muted); text-align: center; }
"""

CSS_CUSTOM_BASE = """
:root {
  --bg: #ffffff;
  --surface: #F1F4F7;
  --surface-2: #EEF2F5;
  --text: #111111;
  --muted: #7A8799;
  --accent: #7C3AED;
  --accent-light: #EDE9FE;
  --border: #E5E7EB;
  --radius: 8px;
  --gap: 1.5rem;
  --font: "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.65; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
.hero { padding: 3rem 0 2rem; border-bottom: 1px solid var(--border); margin-bottom: var(--gap); }
.hero h1 { font-size: clamp(2rem, 5vw, 3rem); font-weight: 700; }
section h2 { font-size: 1.5rem; font-weight: 700; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; }
footer { margin-top: 3rem; border-top: 1px solid var(--border); color: var(--muted); text-align: center; padding-top: 1.5rem; }
"""

# Shared layout rules appended to each preset
CSS_SHARED_LAYOUT = """
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--gap); }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--gap); }
.card ul { list-style: none; padding: 0; }
.card ul li { padding: 0.35rem 0; padding-left: 1rem; position: relative; }
.card ul li::before { content: "·"; position: absolute; left: 0; color: var(--accent); }
ul.bullets { list-style: none; padding: 0; }
ul.bullets li { padding: 0.5rem 0 0.5rem 1.25rem; position: relative; border-bottom: 1px solid var(--border); }
ul.bullets li::before { content: "▸"; position: absolute; left: 0; color: var(--accent); }
.stack-group { margin-bottom: 1rem; }
.stack-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.stack-tag { border-radius: 999px; padding: 0.3rem 0.85rem; font-size: 0.82rem; border: 1px solid var(--border); }
.team-card .role { font-size: 0.85rem; margin-bottom: 0.25rem; }
.incomplete-banner { padding: 0.75rem 1rem; border-radius: var(--radius); margin-bottom: var(--gap); font-size: 0.9rem; }
.hero .meta { color: var(--muted); font-size: 0.95rem; display: flex; flex-wrap: wrap; gap: 1rem; }
@media (max-width: 640px) { .container { padding: 1rem; } }
"""
