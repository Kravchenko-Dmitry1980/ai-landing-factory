"""Exhibition-grade CSS for the WOW landing export (Stage P.7).

Self-contained, profile-aware, no external imports / fonts / CDN. Reuses the
existing ``--alf-*`` theme variables (emitted by ``css_root_block``) and layers a
new ``--wow-*`` visual language on top: cockpit shell, neural grid, radar,
orbiting cards, holographic panels and a pipeline map.
"""

from __future__ import annotations

from app.services.export.theme_tokens import ThemeTokens


def _hex_to_rgba(value: str, alpha: float) -> str:
    """Convert ``#rgb`` / ``#rrggbb`` to ``rgba(...)``; passthrough otherwise."""

    raw = (value or "").strip()
    if raw.startswith("#"):
        hexpart = raw[1:]
        if len(hexpart) == 3:
            hexpart = "".join(ch * 2 for ch in hexpart)
        if len(hexpart) >= 6:
            try:
                r = int(hexpart[0:2], 16)
                g = int(hexpart[2:4], 16)
                b = int(hexpart[4:6], 16)
                return f"rgba({r},{g},{b},{alpha})"
            except ValueError:
                pass
    return raw or f"rgba(124,58,237,{alpha})"


def _wow_vars(tokens: ThemeTokens) -> str:
    dark = tokens.colorScheme == "dark"
    accent = tokens.accent
    grid_line = _hex_to_rgba(accent, 0.16 if dark else 0.10)
    glow = _hex_to_rgba(accent, 0.55 if dark else 0.35)
    radar = _hex_to_rgba(accent, 0.22 if dark else 0.14)

    if dark:
        bg = (
            "radial-gradient(1200px 600px at 80% -10%, "
            f"{_hex_to_rgba(accent, 0.20)}, transparent 60%), "
            "linear-gradient(160deg, #060912 0%, #0b1220 55%, #0a0f1c 100%)"
        )
        panel = "rgba(255,255,255,0.04)"
        panel_border = "rgba(255,255,255,0.10)"
        panel_strong = "rgba(255,255,255,0.07)"
        text = "#e8edf4"
        muted = "#9fb0c6"
    else:
        bg = (
            "radial-gradient(1100px 540px at 85% -10%, "
            f"{_hex_to_rgba(accent, 0.14)}, transparent 55%), "
            "linear-gradient(160deg, #ffffff 0%, #f4f2fb 60%, #eef0fb 100%)"
        )
        panel = "rgba(255,255,255,0.72)"
        panel_border = _hex_to_rgba(accent, 0.22)
        panel_strong = "rgba(255,255,255,0.92)"
        text = "#121327"
        muted = "#5b6478"

    return (
        ".wow-landing{"
        f"--wow-accent:{accent};"
        "--wow-accent-light:var(--alf-accent-light);"
        f"--wow-bg:{bg};"
        f"--wow-grid-line:{grid_line};"
        f"--wow-glow:{glow};"
        f"--wow-radar:{radar};"
        f"--wow-panel:{panel};"
        f"--wow-panel-strong:{panel_strong};"
        f"--wow-panel-border:{panel_border};"
        f"--wow-text:{text};"
        f"--wow-muted:{muted};"
        "}"
    )


# Static rules (no dynamic braces -> safe as a plain string, not an f-string).
_WOW_RULES = """
*{box-sizing:border-box;}
.wow-landing{
  margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  color:var(--wow-text);background:var(--wow-bg);background-attachment:fixed;
  min-height:100vh;line-height:1.55;-webkit-font-smoothing:antialiased;
}
.wow-shell{max-width:1180px;margin:0 auto;padding:0 1.25rem 4rem;}
.wow-landing h1,.wow-landing h2,.wow-landing h3{margin:0 0 .5rem;line-height:1.12;}

/* ===== HERO / COCKPIT ===== */
.wow-hero{position:relative;overflow:hidden;border-radius:28px;margin:1.5rem 0 2.5rem;
  padding:clamp(2rem,5vw,4.5rem) clamp(1.25rem,4vw,3.5rem);
  border:1px solid var(--wow-panel-border);
  background:var(--wow-panel);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  box-shadow:0 24px 80px -40px var(--wow-glow);
}
.wow-cockpit{isolation:isolate;}
.wow-bg-grid{position:absolute;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(var(--wow-grid-line) 1px,transparent 1px),
    linear-gradient(90deg,var(--wow-grid-line) 1px,transparent 1px);
  background-size:46px 46px;
  mask-image:radial-gradient(circle at 30% 20%,#000 0%,transparent 75%);
  -webkit-mask-image:radial-gradient(circle at 30% 20%,#000 0%,transparent 75%);
  animation:wow-grid-pan 24s linear infinite;
}
.wow-bg-radar{position:absolute;top:-30%;right:-12%;width:560px;height:560px;z-index:0;
  pointer-events:none;border-radius:50%;
  background:
    repeating-radial-gradient(circle,var(--wow-radar) 0 1px,transparent 1px 46px),
    radial-gradient(circle,var(--wow-glow),transparent 62%);
  opacity:.55;animation:wow-radar-spin 18s linear infinite;}
.wow-cockpit-shell{position:relative;z-index:2;max-width:760px;}

/* ===== HERO MASCOT (cat assistant — 2D only) ===== */
.wow-hero-mascot{position:absolute;right:clamp(1rem,4vw,3.5rem);top:50%;width:clamp(320px,34vw,520px);
  max-width:46%;aspect-ratio:1;transform:translateY(-50%);z-index:1;pointer-events:none;}
.wow-hero-mascot-glow{position:absolute;left:50%;top:72%;width:76%;height:28%;transform:translate(-50%,-50%);
  border-radius:50%;background:radial-gradient(circle,rgba(167,139,250,.45),rgba(93,214,255,.12) 55%,transparent 72%);
  filter:blur(16px);animation:wow-mascot-glow 5.5s ease-in-out infinite alternate;}
.wow-hero-mascot-platform{position:absolute;left:50%;bottom:6%;width:68%;height:14px;transform:translateX(-50%);
  border-radius:50%;background:linear-gradient(180deg,rgba(255,255,255,.95) 0%,rgba(238,241,251,.85) 100%);
  box-shadow:0 16px 32px -18px rgba(80,70,160,.45),inset 0 1px 0 rgba(255,255,255,.95);}
.wow-hero-mascot-image{position:relative;z-index:2;width:100%;height:auto;object-fit:contain;
  filter:drop-shadow(0 22px 34px rgba(80,70,160,.28));}
.wow-hero-mascot-rig{position:relative;z-index:2;width:100%;animation:wow-cat-float 6.8s ease-in-out infinite;}
.wow-hero-mascot-pose{transform-origin:50% 42%;animation:wow-cat-head-sway 9.5s ease-in-out infinite;}
.wow-hero-mascot-figure{position:relative;width:100%;animation:wow-cat-typing 4.2s ease-in-out infinite;}
.wow-hero-mascot-eyelid{position:absolute;z-index:4;width:10.5%;height:4.2%;border-radius:50%;
  background:rgba(108,118,132,.82);transform-origin:center 20%;transform:scaleY(0);opacity:0;
  animation:wow-cat-blink 7.2s ease-in-out infinite;}
.wow-hero-mascot-eyelid--left{top:28.5%;left:34%;animation-delay:.35s;}
.wow-hero-mascot-eyelid--right{top:28.5%;right:34%;animation-delay:.85s;}
.wow-hero-mascot-medallion{position:absolute;z-index:3;top:49.5%;left:50%;width:10%;height:10%;
  border-radius:50%;transform:translate(-50%,-50%);
  background:radial-gradient(circle,rgba(93,214,255,.75) 0%,rgba(124,77,255,.35) 45%,transparent 72%);
  box-shadow:0 0 18px 4px rgba(93,214,255,.35);mix-blend-mode:screen;
  animation:wow-cat-medallion-pulse 3.4s ease-in-out infinite;}
.wow-hero-mascot-typing-glow{position:absolute;z-index:1;left:38%;bottom:22%;width:28%;height:8%;
  border-radius:8px;background:radial-gradient(circle,rgba(93,214,255,.18),transparent 70%);
  opacity:0;animation:wow-cat-typing-glow 4.2s ease-in-out infinite;}
.wow-hero-ui-card,.wow-hero-ui-icon{position:absolute;z-index:3;border-radius:14px;
  background:rgba(255,255,255,.72);border:1px solid rgba(124,77,255,.16);backdrop-filter:blur(10px);
  box-shadow:0 14px 36px -22px rgba(80,70,160,.65);}
.wow-hero-ui-card--chart{animation:wow-ui-drift-a 7.2s ease-in-out infinite;}
.wow-hero-ui-card--news{animation:wow-ui-drift-b 8.6s ease-in-out infinite;}
.wow-hero-ui-icon--telegram{animation:wow-ui-drift-c 6.4s ease-in-out infinite;}
.wow-hero-ui-card--pie{animation:wow-ui-drift-d 9.1s ease-in-out infinite;}
.wow-hero-ui-card{padding:10px 12px;opacity:.88;}
.wow-hero-ui-card--chart{left:-6%;top:8%;width:72px;height:52px;display:flex;align-items:flex-end;
  justify-content:center;gap:4px;animation-delay:-1.4s;}
.wow-hero-ui-bar{display:block;width:10px;border-radius:4px 4px 2px 2px;
  background:linear-gradient(180deg,rgba(93,214,255,1),var(--wow-accent));}
.wow-hero-ui-bar--1{height:18px;opacity:.55;}
.wow-hero-ui-bar--2{height:28px;}
.wow-hero-ui-bar--3{height:22px;opacity:.75;}
.wow-hero-ui-bar--4{height:34px;}
.wow-hero-ui-card--news{right:-4%;top:22%;width:88px;animation-delay:-2.6s;}
.wow-hero-ui-line{display:block;height:5px;border-radius:999px;background:rgba(124,77,255,.18);margin-bottom:6px;}
.wow-hero-ui-line--title{height:7px;width:70%;background:rgba(124,77,255,.32);}
.wow-hero-ui-line--short{width:55%;margin-bottom:0;}
.wow-hero-ui-icon--telegram{left:4%;bottom:28%;width:38px;height:38px;display:flex;align-items:center;
  justify-content:center;color:#229ed9;border-radius:50%;animation-delay:-.8s;}
.wow-hero-ui-card--pie{right:2%;bottom:18%;width:52px;height:52px;display:flex;align-items:center;
  justify-content:center;animation-delay:-3.2s;}
.wow-hero-ui-pie{width:32px;height:32px;border-radius:50%;
  background:conic-gradient(var(--wow-accent) 0deg 130deg,rgba(93,214,255,1) 130deg 220deg,#d9ccff 220deg 360deg);}
@keyframes wow-mascot-glow{0%{opacity:.75;transform:translate(-50%,-50%) scale(.96);}
  100%{opacity:1;transform:translate(-50%,-50%) scale(1.04);}}
@keyframes wow-cat-float{0%,100%{transform:translateY(0);}50%{transform:translateY(-6px);}}
@keyframes wow-cat-head-sway{0%,100%{transform:rotate(0deg);}32%{transform:rotate(.65deg);}68%{transform:rotate(-.55deg);}}
@keyframes wow-cat-typing{0%,68%,100%{transform:translateY(0);}70%{transform:translateY(1.2px);}71%{transform:translateY(0);}
  72%{transform:translateY(1px);}73%{transform:translateY(0);}74%{transform:translateY(1.2px);}75%,77%{transform:translateY(0);}
  76%{transform:translateY(.8px);}}
@keyframes wow-cat-typing-glow{0%,66%,100%{opacity:0;}70%,78%{opacity:.55;}}
@keyframes wow-cat-blink{0%,90%,100%{transform:scaleY(0);opacity:0;}92%{transform:scaleY(1);opacity:.92;}
  94%{transform:scaleY(.15);opacity:.4;}96%{transform:scaleY(0);opacity:0;}}
@keyframes wow-cat-medallion-pulse{0%,100%{opacity:.42;transform:translate(-50%,-50%) scale(.9);}
  50%{opacity:.92;transform:translate(-50%,-50%) scale(1.1);}}
@keyframes wow-ui-drift-a{0%,100%{transform:translate(0,0);}50%{transform:translate(-3px,-5px);}}
@keyframes wow-ui-drift-b{0%,100%{transform:translate(0,0);}50%{transform:translate(4px,-4px);}}
@keyframes wow-ui-drift-c{0%,100%{transform:translate(0,0);}50%{transform:translate(-2px,3px);}}
@keyframes wow-ui-drift-d{0%,100%{transform:translate(0,0);}50%{transform:translate(3px,4px);}}

.wow-kicker{display:inline-flex;align-items:center;gap:.5rem;
  font-size:.72rem;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
  color:var(--wow-accent);border:1px solid var(--wow-panel-border);
  padding:.4rem .8rem;border-radius:999px;background:var(--wow-panel-strong);}
.wow-kicker::before{content:"";width:8px;height:8px;border-radius:50%;
  background:var(--wow-accent);box-shadow:0 0 12px var(--wow-glow);
  animation:wow-pulse 2.2s ease-in-out infinite;}
.wow-hero h1{font-size:clamp(2.1rem,5.2vw,3.7rem);font-weight:800;margin-top:1.1rem;
  letter-spacing:-.02em;}
.wow-tagline{font-size:clamp(1.02rem,2.2vw,1.3rem);color:var(--wow-muted);max-width:60ch;margin:.6rem 0 0;}
.wow-hero-meta{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1rem;}
.wow-hero-meta span{font-size:.8rem;color:var(--wow-muted);
  border:1px solid var(--wow-panel-border);border-radius:999px;padding:.3rem .7rem;
  background:var(--wow-panel-strong);}
.wow-hero-actions{display:flex;flex-wrap:wrap;gap:.75rem;margin-top:1.6rem;}

/* hero--future-3d perspective tilt */
.hero--future-3d{perspective:1400px;}
.hero--future-3d .wow-cockpit-shell{transform:rotateX(1.5deg);}

/* ===== ORBIT CARDS ===== */
.wow-orbit{position:relative;z-index:2;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.9rem;margin-top:2rem;}
.wow-orbit-card{border:1px solid var(--wow-panel-border);border-radius:16px;
  padding:1rem 1.1rem;background:var(--wow-panel-strong);
  transition:transform var(--alf-motion-duration,.3s) ease,box-shadow var(--alf-motion-duration,.3s) ease;}
.wow-orbit-card:hover{transform:translateY(-5px);box-shadow:0 18px 40px -22px var(--wow-glow);}
.wow-orbit-card .o-value{font-size:1.7rem;font-weight:800;color:var(--wow-accent);}
.wow-orbit-card .o-label{font-size:.8rem;color:var(--wow-muted);text-transform:uppercase;letter-spacing:.08em;}

/* ===== METRIC PANEL ===== */
.wow-section{margin:3rem 0;}
.wow-section-title{font-size:.74rem;letter-spacing:.22em;text-transform:uppercase;
  color:var(--wow-accent);font-weight:700;margin-bottom:1rem;}
.wow-metric-panel{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:1rem;}
.wow-metric-card{position:relative;overflow:hidden;border-radius:18px;padding:1.4rem 1.3rem;
  border:1px solid var(--wow-panel-border);background:var(--wow-panel);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
.wow-metric-card::after{content:"";position:absolute;right:-30px;top:-30px;width:90px;height:90px;
  border-radius:50%;background:var(--wow-glow);filter:blur(28px);opacity:.6;}
.wow-metric-card .m-value{position:relative;z-index:1;font-size:2.1rem;font-weight:800;
  color:var(--wow-text);letter-spacing:-.02em;}
.wow-metric-card .m-label{position:relative;z-index:1;font-size:.92rem;font-weight:600;color:var(--wow-accent);margin-top:.2rem;}
.wow-metric-card .m-hint{position:relative;z-index:1;font-size:.78rem;color:var(--wow-muted);margin-top:.3rem;}

/* ===== PIPELINE MAP ===== */
.wow-pipeline-map{display:flex;flex-wrap:wrap;align-items:stretch;gap:.4rem;}
.wow-pipeline-node{flex:1 1 160px;min-width:150px;border-radius:16px;padding:1.1rem 1rem;
  border:1px solid var(--wow-panel-border);background:var(--wow-panel-strong);
  position:relative;}
.wow-pipeline-node .p-step{font-size:.7rem;font-weight:700;color:var(--wow-accent);letter-spacing:.12em;}
.wow-pipeline-node .p-title{font-size:1.02rem;font-weight:700;margin:.25rem 0 .5rem;}
.wow-pipeline-node .p-tags{display:flex;flex-wrap:wrap;gap:.35rem;}
.wow-pipeline-node .p-tag{font-size:.72rem;color:var(--wow-muted);
  border:1px solid var(--wow-panel-border);border-radius:999px;padding:.15rem .55rem;}
.wow-pipeline-connector{display:flex;align-items:center;justify-content:center;color:var(--wow-accent);
  font-size:1.3rem;flex:0 0 auto;padding:0 .15rem;}

/* ===== HOLOGRAM / MODULES / STACK ===== */
.wow-module-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1rem;}
.wow-hologram-card{position:relative;border-radius:18px;padding:1.3rem;
  border:1px solid var(--wow-panel-border);
  background:linear-gradient(150deg,var(--wow-panel-strong),var(--wow-panel));
  transition:transform var(--alf-motion-duration,.3s) ease;}
.wow-hologram-card:hover{transform:translateY(-4px);}
.wow-hologram-card .h-badge{display:inline-block;font-size:.66rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--wow-accent);border:1px solid var(--wow-panel-border);
  border-radius:999px;padding:.2rem .55rem;margin-bottom:.6rem;}
.wow-hologram-card h3{font-size:1.1rem;}
.wow-hologram-card p{font-size:.9rem;color:var(--wow-muted);margin:.4rem 0 0;}
.wow-stack-cloud{display:flex;flex-direction:column;gap:1rem;}
.wow-stack-group h4{font-size:.85rem;color:var(--wow-muted);text-transform:uppercase;letter-spacing:.1em;margin:0 0 .5rem;}
.wow-stack-chips{display:flex;flex-wrap:wrap;gap:.45rem;}
.wow-chip{font-size:.82rem;border:1px solid var(--wow-panel-border);border-radius:10px;
  padding:.35rem .7rem;background:var(--wow-panel-strong);color:var(--wow-text);}
.wow-chip.is-core{border-color:var(--wow-accent);color:var(--wow-accent);
  box-shadow:0 0 14px -4px var(--wow-glow);font-weight:600;}

/* ===== CTA ===== */
.wow-demo-cta{margin:3.5rem 0 1rem;border-radius:24px;padding:clamp(1.8rem,4vw,3rem);
  border:1px solid var(--wow-panel-border);text-align:center;
  background:linear-gradient(135deg,var(--wow-panel-strong),var(--wow-panel));
  box-shadow:0 28px 80px -50px var(--wow-glow);}
.wow-demo-cta h2{font-size:clamp(1.5rem,3vw,2.1rem);font-weight:800;}
.wow-demo-cta p{color:var(--wow-muted);max-width:54ch;margin:.6rem auto 1.5rem;}
.wow-cta-actions{display:flex;flex-wrap:wrap;gap:.75rem;justify-content:center;}
.wow-btn{display:inline-flex;align-items:center;gap:.5rem;font-size:.95rem;font-weight:600;
  text-decoration:none;border-radius:12px;padding:.8rem 1.4rem;cursor:pointer;border:1px solid transparent;
  transition:transform var(--alf-motion-duration,.3s) ease,box-shadow var(--alf-motion-duration,.3s) ease;}
.wow-btn.primary{background:var(--wow-accent);color:#fff;box-shadow:0 14px 34px -16px var(--wow-glow);}
.wow-btn.primary:hover{transform:translateY(-2px);}
.wow-btn.secondary{background:var(--wow-panel-strong);color:var(--wow-text);border-color:var(--wow-panel-border);}
.wow-btn.secondary:hover{transform:translateY(-2px);}
.wow-btn.is-disabled{opacity:.5;cursor:not-allowed;pointer-events:none;}

/* ===== A-FRAME EMBED ===== */
.wow-aframe-hero{position:relative;z-index:2;margin-top:1.6rem;border-radius:18px;overflow:hidden;
  border:1px solid var(--wow-panel-border);height:300px;background:#05070f;}
.wow-aframe-hero a-scene{width:100%;height:100%;}
.wow-aframe-fallback{font-size:.8rem;color:var(--wow-muted);margin-top:.5rem;}

/* ===== FOOTER ===== */
.wow-footer{margin-top:3rem;padding-top:1.4rem;border-top:1px solid var(--wow-panel-border);
  font-size:.82rem;color:var(--wow-muted);text-align:center;}

/* ===== ANIMATIONS ===== */
@keyframes wow-grid-pan{from{background-position:0 0,0 0;}to{background-position:46px 46px,46px 46px;}}
@keyframes wow-radar-spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
@keyframes wow-pulse{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.5);opacity:.5;}}

/* ===== RESPONSIVE ===== */
@media (max-width:720px){
  .wow-hero{border-radius:20px;}
  .wow-hero-mascot{right:50%;top:auto;bottom:10px;width:min(240px,72vw);max-width:88%;transform:translateX(50%);}
  .wow-hero-ui-card,.wow-hero-ui-icon{display:none;}
  .wow-cockpit-shell{padding-bottom:clamp(140px,34vw,200px);}
  .wow-pipeline-connector{transform:rotate(90deg);width:100%;flex-basis:100%;}
  .wow-pipeline-node{flex-basis:100%;}
  .wow-bg-radar{display:none;}
}

/* ===== ACCESSIBILITY: reduced motion ===== */
@media (prefers-reduced-motion:reduce){
  .wow-bg-grid,.wow-bg-radar,.wow-kicker::before,.wow-hero-mascot-glow,.wow-hero-mascot-rig,
  .wow-hero-mascot-pose,.wow-hero-mascot-figure,.wow-hero-mascot-eyelid,.wow-hero-mascot-medallion,
  .wow-hero-mascot-typing-glow,.wow-hero-ui-card,.wow-hero-ui-icon{animation:none!important;}
  .wow-orbit-card,.wow-hologram-card,.wow-btn{transition:none!important;}
}

/* ===== PRINT SAFE ===== */
@media print{
  .wow-landing{background:#fff!important;color:#000!important;}
  .wow-bg-grid,.wow-bg-radar,.wow-aframe-hero{display:none!important;}
  .wow-hero,.wow-metric-card,.wow-pipeline-node,.wow-hologram-card,.wow-demo-cta{
    box-shadow:none!important;border-color:#ccc!important;background:#fff!important;}
}
"""


def build_wow_css(tokens: ThemeTokens) -> str:
    """Return the full WOW stylesheet (root vars + wow scoped vars + rules)."""

    from app.services.export.theme_tokens import css_root_block

    return css_root_block(tokens) + _wow_vars(tokens) + _WOW_RULES
