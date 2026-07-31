"""
NeuroSync — Extraction Noise Probe (tracker D2).

Measures what the NER + embedding-discovery layers emit as "skills" and what
they write into the in-memory taxonomy. Run before and after a change and diff
the output — the tracker requires before/after numbers, not assertions.

Usage (from core/backend/):
    ./venv/Scripts/python.exe tools/noise_probe.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.pipeline_probe import JD, RESUME  # noqa: E402  (path set above)

# Terms that are demonstrably not skills. Anything here reaching the extracted
# set or the taxonomy is a D2 false positive. Kept as substrings-of-interest so
# variants ("Designed Postgresql") are caught without listing every inflection.
NOISE_MARKERS = (
    "mentored", "designed", "built", "implemented", "developed", "led ",
    "integrated", "computer science", "university", "b.tech", "cgpa",
    "techcorp", "startupxyz", "junior", "requirements", "nice to have",
    "we offer", "competitive", "years of experience", "strong ", "senior ",
)

# Action verbs that must never survive as skills — the exact D2 failure mode.
HARD_NOISE = {
    "mentored", "designed postgresql", "computer science", "event-driven",
    "infrastructure-as-code", "built", "designed", "implemented", "developed",
    "led", "integrated",
}


def looks_noisy(name: str) -> bool:
    low = name.lower().strip()
    if low in HARD_NOISE:
        return True
    return any(m in low for m in NOISE_MARKERS)


def main() -> int:
    logging.getLogger().setLevel(logging.WARNING)

    from app.api.deps import (
        get_embedding_store, get_extractor, get_semantic_model, get_taxonomy,
    )

    taxonomy = get_taxonomy()
    static_count = len(taxonomy._entries)

    # Warm the embedding store so Layer 4 actually runs (lifespan does this in prod).
    get_semantic_model()
    get_embedding_store()
    extractor = get_extractor()

    resume = extractor.extract(RESUME)
    jd = extractor.extract(JD)

    print("=" * 72)
    print("D2 — EXTRACTION NOISE")
    print("=" * 72)
    print(f"  static taxonomy skills   {static_count}")
    print(f"  resume skills extracted  {len(resume.skills)}")
    print(f"  jd skills extracted      {len(jd.skills)}")
    print()

    # ---- Per-layer output, flagging noise -------------------------------
    total_noise = 0
    for label, result in (("RESUME", resume), ("JD", jd)):
        by_method: dict[str, list] = {}
        for s in result.skills:
            by_method.setdefault(s.matched_by.value, []).append(s)

        print(f"  {label} — skills by layer")
        for method in ("taxonomy", "ner", "semantic", "embedding_discovery"):
            skills = by_method.get(method, [])
            if not skills:
                continue
            noisy = [s for s in skills if looks_noisy(s.canonical)]
            total_noise += len(noisy)
            print(f"    {method:<20} {len(skills):>3} skills, "
                  f"{len(noisy)} noisy")
            for s in sorted(skills, key=lambda x: x.canonical):
                flag = "  <-- NOISE" if looks_noisy(s.canonical) else ""
                if flag or method != "taxonomy":
                    print(f"       {s.canonical:<34} {s.category.value:<12}"
                          f"conf={s.confidence:.2f}{flag}")
        print()

    # ---- Taxonomy writes -------------------------------------------------
    runtime = dict(taxonomy._runtime_skills)
    provisional = getattr(taxonomy, "_provisional", {})

    print(f"  taxonomy writes (promoted)    {len(runtime)}")
    print(f"  taxonomy writes (provisional) {len(provisional)}")
    print()

    if runtime:
        print("  PROMOTED — visible to every later analysis in this process:")
        for norm, entry in sorted(runtime.items()):
            flag = "  <-- NOISE" if looks_noisy(entry.canonical) else ""
            print(f"    {entry.canonical:<34} {entry.category.value:<12}{flag}")
    else:
        print("  PROMOTED: (none)")
    print()

    if provisional:
        print("  PROVISIONAL — quarantined, not yet part of the taxonomy:")
        for norm, prov in sorted(provisional.items()):
            entry = prov.entry if hasattr(prov, "entry") else prov
            sightings = len(getattr(prov, "documents", ()) or ())
            print(f"    {entry.canonical:<34} {entry.category.value:<12}"
                  f"sightings={sightings}")
    print()

    noisy_promoted = sorted(n for n, e in runtime.items()
                            if looks_noisy(e.canonical))

    print("=" * 72)
    print(f"VERDICT: {len(noisy_promoted)} noise terms promoted into the taxonomy"
          f" | {total_noise} noisy skills emitted across both documents")
    if noisy_promoted:
        print(f"         promoted noise: {', '.join(noisy_promoted)}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
