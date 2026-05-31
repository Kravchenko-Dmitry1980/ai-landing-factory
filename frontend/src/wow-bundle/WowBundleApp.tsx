/**
 * Standalone Interactive WOW Bundle app (Stage P.7.2).
 *
 * Renders a full-screen R3F WOW hero plus data-driven sections (impact metrics,
 * pipeline, systems/modules, stack, team, CTA). Built into a portable bundle by
 * `frontend/scripts/build-wow-bundle.mjs` — no Next router, no API client.
 *
 * The heavy R3F scene is `lazy()`-loaded so this module's static import graph
 * stays free of `three`/`@react-three/fiber`; that keeps it server-renderable in
 * the test environment (no WebGL) where it falls back to a static hero.
 */

import { Suspense, lazy, useMemo } from "react";
import {
  buildSceneNodes,
  type WowBundleData,
} from "./WowBundleData";
import { WowHeroMascot } from "@/components/wow/WowHeroMascot";
import { WOW_BUNDLE_BUILD_MARKER, WOW_BUNDLE_CAT_MASCOT_SRC } from "@/components/wow/wowMascotAsset";

const WowBundleRenderer = lazy(() => import("./WowBundleRenderer"));

interface Props {
  data: WowBundleData;
  /** Force-disable WebGL (tests / no-WebGL environments). */
  enable3d?: boolean;
  reducedMotion?: boolean;
}

function detectWebGL(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      canvas.getContext("webgl2") ||
        canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl"),
    );
  } catch {
    return false;
  }
}

function detectReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

function StaticHeroBackdrop() {
  return <div className="wow-hero__static" aria-hidden="true" />;
}

function HeroChips({ data }: { data: WowBundleData }) {
  const chips: Array<{ label: string; value: string }> = [];
  if (data.project.client) chips.push({ label: "Клиент", value: data.project.client });
  if (data.project.period) chips.push({ label: "Период", value: data.project.period });
  if (data.project.lead) chips.push({ label: "Лид", value: data.project.lead });
  if (chips.length === 0) return null;
  return (
    <ul className="wow-chips">
      {chips.map((c) => (
        <li key={c.label} className="wow-chip">
          <span className="wow-chip__label">{c.label}</span>
          <span className="wow-chip__value">{c.value}</span>
        </li>
      ))}
    </ul>
  );
}

function HeroCta({ data }: { data: WowBundleData }) {
  const { demo_url, showcase_url } = data.links;
  if (!demo_url && !showcase_url) {
    return (
      <p className="wow-cta__fallback">
        Демо-ссылка появится после публикации проекта.
      </p>
    );
  }
  return (
    <div className="wow-cta">
      {demo_url && (
        <a className="wow-btn wow-btn--primary" href={demo_url} rel="noopener noreferrer">
          Открыть демо
        </a>
      )}
      {showcase_url && (
        <a className="wow-btn wow-btn--ghost" href={showcase_url} rel="noopener noreferrer">
          Витрина проекта
        </a>
      )}
    </div>
  );
}

function MetricCards({
  data,
  limit,
  className,
}: {
  data: WowBundleData;
  limit?: number;
  className: string;
}) {
  const metrics = limit ? data.metrics.slice(0, limit) : data.metrics;
  if (metrics.length === 0) return null;
  return (
    <div className={className}>
      {metrics.map((m, i) => (
        <div key={`${m.label}-${i}`} className="wow-metric">
          <span className="wow-metric__value">{m.value}</span>
          <span className="wow-metric__label">{m.label}</span>
          {m.hint && <span className="wow-metric__hint">{m.hint}</span>}
        </div>
      ))}
    </div>
  );
}

export function WowBundleApp({ data, enable3d, reducedMotion }: Props) {
  const nodes = useMemo(() => buildSceneNodes(data), [data]);
  const accent = data.theme.accent ?? "#7c8bff";
  const use3d = enable3d ?? detectWebGL();
  const reduce = reducedMotion ?? detectReducedMotion();

  return (
    <div
      className="wow-bundle"
      data-profile={data.theme.profile}
      data-wow-build={WOW_BUNDLE_BUILD_MARKER}
      style={{ ["--wow-accent" as string]: accent } as React.CSSProperties}
    >
      <section className="wow-hero">
        <div className="wow-hero__bg">
          {use3d ? (
            <Suspense fallback={<StaticHeroBackdrop />}>
              <WowBundleRenderer nodes={nodes} accent={accent} reducedMotion={reduce} />
            </Suspense>
          ) : (
            <StaticHeroBackdrop />
          )}
        </div>
        <div className="wow-hero__overlay">
          <span className="wow-hero__eyebrow">AI-витрина · 3D-экспонат</span>
          <h1 className="wow-hero__title">{data.project.title}</h1>
          {data.project.subtitle && (
            <p className="wow-hero__subtitle">{data.project.subtitle}</p>
          )}
          <HeroChips data={data} />
          <MetricCards data={data} limit={4} className="wow-hero__metrics" />
          <HeroCta data={data} />
        </div>
        <WowHeroMascot src={WOW_BUNDLE_CAT_MASCOT_SRC} className="wow-hero__mascot" />
        <div className="wow-hero__scrollhint" aria-hidden="true">
          ↓ прокрутите вниз
        </div>
      </section>

      {data.metrics.length > 0 && (
        <section className="wow-section wow-section--impact" id="impact">
          <h2 className="wow-section__title">Impact в цифрах</h2>
          <MetricCards data={data} className="wow-impact-grid" />
        </section>
      )}

      {data.pipeline.length > 0 && (
        <section className="wow-section wow-section--pipeline" id="pipeline">
          <h2 className="wow-section__title">Pipeline системы</h2>
          <ol className="wow-pipeline">
            {data.pipeline.map((stage, i) => (
              <li key={`${stage.title}-${i}`} className="wow-pipeline__stage">
                <span className="wow-pipeline__index">{i + 1}</span>
                <span className="wow-pipeline__name">{stage.title}</span>
                {stage.tags && stage.tags.length > 0 && (
                  <span className="wow-pipeline__tags">
                    {stage.tags.map((t) => (
                      <span key={t} className="wow-tag">
                        {t}
                      </span>
                    ))}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      {data.modules.length > 0 && (
        <section className="wow-section wow-section--modules" id="modules">
          <h2 className="wow-section__title">Подсистемы и модули</h2>
          <div className="wow-modules-grid">
            {data.modules.map((m, i) => (
              <article key={`${m.title}-${i}`} className="wow-card">
                <h3 className="wow-card__title">{m.title}</h3>
                {m.type && <span className="wow-card__badge">{m.type}</span>}
                {m.description && <p className="wow-card__body">{m.description}</p>}
              </article>
            ))}
          </div>
        </section>
      )}

      {data.stack.length > 0 && (
        <section className="wow-section wow-section--stack" id="stack">
          <h2 className="wow-section__title">Технологический стек</h2>
          <div className="wow-stack">
            {data.stack.map((group) => (
              <div key={group.group} className="wow-stack__group">
                <h3 className="wow-stack__title">{group.group}</h3>
                <div className="wow-stack__chips">
                  {group.items.map((item) => (
                    <span key={item} className="wow-tag wow-tag--lg">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {data.team.length > 0 && (
        <section className="wow-section wow-section--team" id="team">
          <h2 className="wow-section__title">Команда</h2>
          <div className="wow-team">
            {data.team.map((member, i) => (
              <div key={`${member.name}-${i}`} className="wow-team__member">
                <span className="wow-team__name">{member.name}</span>
                {member.role && <span className="wow-team__role">{member.role}</span>}
                {member.area && <span className="wow-team__area">{member.area}</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="wow-section wow-section--cta" id="cta">
        <h2 className="wow-section__title">{data.project.title}</h2>
        <HeroCta data={data} />
        <p className="wow-footer-note">
          Интерактивный демонстрационный артефакт · работает офлайн, без backend.
        </p>
      </section>
    </div>
  );
}

export default WowBundleApp;
