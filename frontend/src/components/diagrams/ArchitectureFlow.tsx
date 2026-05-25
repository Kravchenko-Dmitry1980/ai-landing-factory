"use client";

import { motion } from "framer-motion";
import type { RenderPlan } from "@/rendering/types";

interface Props {
  plan: RenderPlan;
  inputs: string[];
  outputs: string[];
}

export function ArchitectureFlow({ plan, inputs, outputs }: Props) {
  const nodes = [
    { id: "in", label: "Inputs", items: inputs.slice(0, 5) },
    { id: "core", label: "Processing", items: ["Extraction", "PII Guard", "Contract"] },
    { id: "out", label: "Outputs", items: outputs.slice(0, 5) },
  ];

  const reveal = plan.profile.motion.enableNodeReveal;

  return (
    <div
      className="grid gap-4 md:grid-cols-3"
      role="img"
      aria-label="Architecture flow diagram"
    >
      {nodes.map((node, i) => (
        <motion.div
          key={node.id}
          initial={reveal ? { opacity: 0, y: 6 } : false}
          whileInView={reveal ? { opacity: 1, y: 0 } : undefined}
          viewport={{ once: true }}
          transition={{ delay: i * 0.08 }}
          className="rounded-md border border-[var(--alf-border)] bg-[var(--alf-surface)] p-4"
        >
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--alf-accent)]">
            {node.label}
          </p>
          <ul className="mt-3 space-y-1.5 text-sm text-[var(--alf-text)]">
            {node.items.map((item) => (
              <li key={item} className="border-l-2 border-[var(--alf-accent-muted)] pl-2">
                {item}
              </li>
            ))}
          </ul>
        </motion.div>
      ))}
    </div>
  );
}
