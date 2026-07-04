# Fidelity checklist — the verify gate for anything outward-facing

> The fidelity-verifier agent runs this file against every draft before the human gate.
> Editing this file changes the gate; that is the point. Add your own checks at the
> bottom; org-specific boundaries belong in domain-rules.md.

A draft **fails** on any BLOCK finding. When unsure whether something is a finding,
it is a finding.

1. **Premise truth** — the opening states nothing untrue as setup. No manufactured
   "every organisation struggles with X" unless it is actually established. BLOCK.
2. **Stance / epistemic fidelity** — exploration is not presented as decision;
   a brainstorm is not presented as a position taken; a hypothetical is labelled.
   Getting facts right while misrepresenting *intent* or *status* is still a fail. BLOCK.
3. **Stage accuracy** — the stage line (thought piece / vision / options explored /
   prototype / in production) matches what the sources support. Inflation by one rung
   is the single biggest credibility risk. BLOCK.
4. **Grounding** — every load-bearing claim traces to a cited source page; quotes and
   numbers verified exactly. BLOCK.
5. **Sensitivity / shield** — nothing shielded (do-not-syndicate or config markers),
   nothing `hold`-tier, no secrets, no personal data beyond what the tier permits. BLOCK.
6. **Voice / AI-tells** — announced honesty, hype adjectives, em-dash overload,
   symmetric listicles, empty hedges. WARN (BLOCK if pervasive).
7. **Domain rules** — every rule in domain-rules.md, checked verbatim. BLOCK each.
