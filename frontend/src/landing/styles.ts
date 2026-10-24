/** CSS of the v2 landing template. One stylesheet for both themes; the screen is always dark. */

export interface RunTiming {
  /** Seconds of one full animation cycle of the hero screen. */
  cycle: number;
  /** Percent of the cycle at which step i lights up. */
  stepAt: number[];
}

const STEP_SECONDS = 1;
const LEAD_IN = 0.6;
const HOLD = 4;

export function runTiming(steps: number): RunTiming {
  const cycle = LEAD_IN + steps * STEP_SECONDS + HOLD;
  const stepAt = Array.from({ length: steps }, (_, i) => ((LEAD_IN + i * STEP_SECONDS) / cycle) * 100);
  return { cycle, stepAt };
}

const pct = (n: number) => `${Math.min(100, Math.max(0, n)).toFixed(2)}%`;

/** Per-step keyframes: each step lights at its moment and everything resets together at the end. */
function runKeyframes({ stepAt }: RunTiming): string {
  const rows = stepAt
    .map(
      (at, i) => `
@keyframes run-row-${i}{0%,${pct(at)}{opacity:.42;transform:translateX(0)}${pct(at + 1.5)},92%{opacity:1;transform:translateX(4px)}97%,100%{opacity:.42;transform:translateX(0)}}
@keyframes run-dot-${i}{0%,${pct(at)}{background:#22304A;box-shadow:none}${pct(at + 1.5)},92%{background:#3FDCFF;box-shadow:0 0 12px rgba(63,220,255,.75)}97%,100%{background:#22304A;box-shadow:none}}
.run__step--${i}{animation:run-row-${i} var(--cycle) ease-out infinite}
.run__step--${i} .run__dot{animation:run-dot-${i} var(--cycle) ease-out infinite}
.run__step--${i} .run__done{animation:run-done-${i} var(--cycle) ease-out infinite}
@keyframes run-done-${i}{0%,${pct(at + 1)}{opacity:0}${pct(at + 2.5)},92%{opacity:1}97%,100%{opacity:0}}`,
    )
    .join("");
  const first = stepAt[0] ?? 0;
  const last = stepAt[stepAt.length - 1] ?? 0;
  return `${rows}
@keyframes run-progress{0%,${pct(first)}{width:0}${pct(last + 3)},92%{width:100%}97%,100%{width:0}}
@keyframes run-toast{0%,${pct(last + 4)}{opacity:0;transform:translateY(-10px) scale(.97)}${pct(last + 8)},91%{opacity:1;transform:none}96%,100%{opacity:0;transform:translateY(-6px)}}`;
}

export function landingCss(timing: RunTiming): string {
  return `
:root{color-scheme:dark;--bg:#0A0F1C;--hero:#0C1222;--band:#0D1424;--panel:#111A2D;--grid:rgba(122,164,255,.06);--line:#1C2841;--line2:#2A3A5C;--ink:#EEF2FA;--ink2:#B9C4D9;--muted:#8A98B4;--figure:#3FDCFF;--bad:#FF8FA0;--track:#1B2740;--cta:#3FDCFF;--cta-ink:#04202A;--chip:#131D33;--bezel:rgba(122,164,255,.08);--cycle:${timing.cycle.toFixed(2)}s}
:root[data-theme=light]{color-scheme:light;--bg:#FFFFFF;--hero:#F6F7FB;--band:#F6F7FB;--panel:#FFFFFF;--grid:#E9EDF5;--line:#E2E7F1;--line2:#C9D2E3;--ink:#1B2029;--ink2:#3A404B;--muted:#5F6673;--figure:#1E5FD8;--bad:#C42E47;--track:#E7EBF3;--cta:#1E5FD8;--cta-ink:#FFFFFF;--chip:#FFFFFF;--bezel:#E2E7F1}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 "Golos Text",system-ui,sans-serif;-webkit-font-smoothing:antialiased;overflow-x:hidden}
img{max-width:100%}
a{color:var(--figure)}
h1,h2,h3{font-family:"Geologica Variable","Geologica",system-ui,sans-serif;font-weight:700;margin:0;letter-spacing:-.025em}
h2{font-size:clamp(30px,4vw,44px);line-height:1.08}
h3{font-size:20px;letter-spacing:-.01em;line-height:1.25}
p{margin:0}
.wrap{max-width:1220px;margin:0 auto;padding:0 24px}
.band{background:var(--band)}
.sec{padding:88px 0;border-bottom:1px solid var(--line)}
.sec__head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:16px 40px;margin-bottom:36px}
.sec__note{max-width:440px;color:var(--ink2)}
.top{border-bottom:1px solid var(--line)}
.top__in{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding-top:14px;padding-bottom:14px}
.brand{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--muted)}
.brand img{width:36px;height:36px;object-fit:contain}
.top nav{display:flex;gap:28px;flex-wrap:wrap;font-size:15px}
.top nav a{color:var(--ink);text-decoration:none}
.top nav a:hover{color:var(--figure)}
.hero{overflow-x:clip;background-color:var(--hero);background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:32px 32px;border-bottom:1px solid var(--line)}
.hero__in{display:flex;flex-wrap:wrap;gap:56px;align-items:center;padding-top:72px;padding-bottom:96px}
.hero__text{flex:1 1 420px;min-width:0;display:flex;flex-direction:column;gap:28px}
.hero h1{font-size:clamp(38px,5.2vw,62px);line-height:1.02;letter-spacing:-.035em;hyphens:auto;overflow-wrap:anywhere}
.lead{font-size:20px;line-height:1.55;max-width:560px;color:var(--ink2)}
.facts{display:flex;flex-wrap:wrap;gap:12px 36px;margin:0;font-size:15px}
.facts dt{color:var(--muted)}
.facts dd{margin:4px 0 0;font-weight:600}
.cta{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;min-height:50px;padding:0 22px;border-radius:12px;border:1px solid var(--line2);color:var(--ink);text-decoration:none;font-weight:600}
.btn--main{background:var(--cta);border-color:var(--cta);color:var(--cta-ink)}
.screen{flex:1.3 1 520px;min-width:0;position:relative;margin:0 0 40px}
.screen__frame{position:relative;border-radius:22px;background:#0B1222;border:1px solid #22304A;box-shadow:0 40px 80px -30px rgba(5,10,25,.7),0 0 0 6px var(--bezel);overflow:hidden;color:#DCE6F7}
.screen__bar{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 18px;border-bottom:1px solid #1B2740;font-size:13px;color:#8FA0BF}
.live{display:flex;align-items:center;gap:8px}
.live i{width:9px;height:9px;border-radius:50%;background:#3FDCFF;box-shadow:0 0 10px #3FDCFF;animation:blink 1.4s steps(2) infinite}
.screen__body{position:relative;padding:22px 22px 18px;background-image:linear-gradient(rgba(122,164,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(122,164,255,.05) 1px,transparent 1px);background-size:20px 20px;overflow:hidden}
.scan{position:absolute;left:0;right:0;top:0;height:46px;background:linear-gradient(rgba(63,220,255,0),rgba(63,220,255,.14));border-bottom:2px solid rgba(63,220,255,.7);animation:scan 3.4s linear infinite;pointer-events:none}
.run{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px;position:relative}
.run__step{display:grid;grid-template-columns:18px minmax(0,1fr) auto;gap:14px;align-items:center;padding:12px 14px;border-radius:12px;background:rgba(17,26,45,.85);border:1px solid #1B2740;opacity:.42}
.run__dot{width:12px;height:12px;border-radius:50%;background:#22304A}
.run__text{display:flex;flex-direction:column;min-width:0}
.run__text b{font-weight:600;font-size:15px;line-height:1.3;color:#EEF2FA}
.run__text small{font-size:13px;line-height:1.35;color:#8FA0BF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.run__done{font-size:12px;color:#3FDCFF;opacity:0}
.screen__progress{height:6px;margin-top:16px;border-radius:3px;background:#1B2740;overflow:hidden}
.screen__progress span{display:block;height:100%;width:0;background:#3FDCFF;box-shadow:0 0 12px #3FDCFF;animation:run-progress var(--cycle) ease-in-out infinite}
.toast{position:absolute;right:18px;bottom:40px;width:min(270px,80%);padding:14px 16px;border-radius:14px;background:rgba(6,18,30,.94);border:1px solid #3FDCFF;box-shadow:0 0 26px rgba(63,220,255,.3);opacity:0;animation:run-toast var(--cycle) cubic-bezier(.2,.8,.2,1) infinite}
.toast b{display:block;font-family:"Geologica Variable","Geologica",sans-serif;font-size:30px;line-height:1.05;letter-spacing:-.02em;color:#3FDCFF}
.toast span{display:block;margin-top:6px;font-size:13px;line-height:1.4;color:#C9D6EC}
.cat{display:block;background:var(--cat) center/contain no-repeat}
.screen__cat{position:absolute;right:-40px;bottom:-34px;width:180px;height:180px;filter:drop-shadow(0 18px 24px rgba(0,0,0,.35));animation:float 6s ease-in-out infinite}
.results{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:20px}
.card{padding:26px;border-radius:22px;background:var(--panel);border:1px solid var(--line)}
.change{grid-row:span 2;display:flex;flex-direction:column;gap:20px;padding:32px}
.bar{display:flex;flex-direction:column;gap:8px}
.bar__label{display:flex;justify-content:space-between;gap:12px;font-size:15px;color:var(--ink2)}
.bar__label strong{font-variant-numeric:tabular-nums}
.bar__track{height:18px;border-radius:9px;background:var(--track)}
.bar__fill{height:100%;border-radius:9px;min-width:8px}
.change__big{margin-top:auto;font-family:"Geologica Variable","Geologica",sans-serif;font-weight:700;font-size:clamp(44px,5vw,64px);line-height:.98;letter-spacing:-.04em;color:var(--figure)}
.metric{display:flex;align-items:center;gap:22px}
.ring{flex:none;width:104px;height:104px;transform:rotate(-90deg)}
.metric__value{font-family:"Geologica Variable","Geologica",sans-serif;font-weight:700;font-size:40px;line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.metric__label{font-weight:600;margin-top:8px;line-height:1.3}
.metric__detail{font-size:14px;line-height:1.45;color:var(--muted);margin-top:4px}
.notes{margin:28px 0 0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:12px 40px}
.notes li,.points li{display:grid;grid-template-columns:22px minmax(0,1fr);gap:12px;line-height:1.55}
.notes li::before,.points li::before{content:"";margin-top:9px;width:10px;height:10px;border-radius:50%;border:2px solid var(--figure)}
.points{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:14px}
.two{display:flex;flex-wrap:wrap;gap:56px}
.two>*{flex:1 1 420px;min-width:0}
.h-gap{margin-bottom:24px}
.intro{display:flex;flex-direction:column;gap:10px;max-width:72ch;margin:0 0 28px;color:var(--ink2)}
.essence{font-size:18px;line-height:1.7;color:var(--ink2);max-width:68ch;display:flex;flex-direction:column;gap:14px}
.io{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:20px}
.io h3{margin-bottom:14px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:20px}
.steps .card{display:flex;flex-direction:column;gap:10px;border-top:3px solid var(--figure)}
.steps p{color:var(--ink2);font-size:16px;line-height:1.55}
.stack{display:flex;flex-direction:column;gap:20px}
.stack__name{font-size:14px;color:var(--muted);margin-bottom:8px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips span{padding:6px 12px;border-radius:999px;border:1px solid var(--line2);background:var(--chip);font-size:14px}
.team{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(270px,100%),1fr));gap:18px}
.person{display:flex;flex-direction:column;gap:12px}
.person__head{display:flex;gap:12px;align-items:center}
.avatar{flex:none;width:46px;height:46px;border-radius:50%;border:2px solid var(--figure);display:flex;align-items:center;justify-content:center;font-weight:600;font-size:15px}
.person--lead{border-color:var(--figure)}
.person--lead .avatar{background:var(--figure);color:var(--cta-ink)}
.person__name{font-weight:600;line-height:1.3}
.person__role{font-size:14px;line-height:1.4;color:var(--muted)}
.person details{font-size:14px;color:var(--ink2)}
.person summary{cursor:pointer;color:var(--figure)}
.person ul{margin:8px 0 0;padding-left:18px;display:flex;flex-direction:column;gap:6px;line-height:1.45}
.outlook{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:12px;max-width:820px}
.foot{position:relative;margin-top:60px;background:var(--band);border-top:1px solid var(--line)}
.foot__in{display:flex;align-items:center;gap:28px;flex-wrap:wrap;padding-top:36px;padding-bottom:44px}
.foot__cat{flex:none;width:150px;height:150px;margin-top:-86px;filter:drop-shadow(0 14px 20px rgba(0,0,0,.3))}
.foot b{display:block;font-family:"Geologica Variable","Geologica",sans-serif;font-size:24px;letter-spacing:-.01em}
.foot span{color:var(--muted);font-size:15px}
@keyframes scan{0%{transform:translateY(-50px)}100%{transform:translateY(520px)}}
@keyframes blink{0%{opacity:1}100%{opacity:.2}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
${runKeyframes(timing)}
@media (max-width:1100px){.screen__cat{right:-6px}}
@media (max-width:720px){.hero__in{padding-top:44px;padding-bottom:64px;gap:40px}.screen__cat{width:120px;height:120px;right:-8px;bottom:-30px}.sec{padding:64px 0}.lead{font-size:18px}}
@media (prefers-reduced-motion:reduce){*,*::before{animation:none!important;scroll-behavior:auto!important}.run__step{opacity:1}.run__dot{background:#3FDCFF}.run__done{opacity:1}.screen__progress span{width:100%}.toast{opacity:1;position:static;width:auto;margin-top:16px}.scan{display:none}}
`;
}
