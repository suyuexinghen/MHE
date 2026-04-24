# Tested Support Matrix Template

Use this template when docs need a tested support matrix tied to current evidence.

```markdown
| Family | Contract / Compiler Surface | Runtime / Evidence Coverage | Diagnostics / Policy / Governance Coverage | Test Anchor | Caveat / Not Yet Proven | Status |
|---|---|---|---|---|---|---|
| hofx | ... | ... | ... | ... | ... | tested / partial / planned |
| forecast | ... | ... | ... | ... | ... | tested / partial / planned |
```

Rules:
- only mark a row as `tested` when corresponding automated or directly reviewed evidence exists
- use `partial` when only some seams are covered
- use `planned` when support is still design intent rather than landed coverage
- keep the matrix aligned with current handoff and roadmap truth
- include a concrete test anchor or directly reviewed evidence hook for each non-planned row
