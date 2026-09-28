"use client";

import { useState } from "react";
import type { Citation } from "@/lib/api";

type Props = {
  citations: Citation[];
};

export default function CitationList({ citations }: Props) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const open = citations.find((c) => c.index === openIndex) ?? null;

  return (
    <div className="mt-2">
      <ul className="flex flex-wrap gap-1.5" aria-label="Sources">
        {citations.map((citation) => {
          const active = citation.index === openIndex;
          return (
            <li key={citation.index}>
              <button
                type="button"
                aria-expanded={active}
                onClick={() => setOpenIndex(active ? null : citation.index)}
                className={`rounded-full border px-2.5 py-0.5 text-xs transition-colors ${
                  active
                    ? "border-blue-600 bg-blue-600 text-white"
                    : "border-neutral-300 bg-white text-neutral-700 hover:border-neutral-500"
                }`}
              >
                [{citation.index}] {citation.document} · p. {citation.page}
              </button>
            </li>
          );
        })}
      </ul>
      {open && (
        <blockquote
          className="mt-2 rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-xs leading-relaxed text-neutral-700"
          data-testid="citation-snippet"
        >
          <p className="mb-1 font-medium text-neutral-500">
            {open.document}, page {open.page}
          </p>
          {open.snippet}
        </blockquote>
      )}
    </div>
  );
}
