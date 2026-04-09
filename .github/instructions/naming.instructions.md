---
applyTo: "**"
description: >
  Naming conventions for the wz_local suite.
  Authoritative standard: WZ2/Standards/naming.md
  Suite prefix: wz (declared in suite.json → "prefix")
  App code: wtrack (declared in suite.json → subprojects[].appcode)
---

# Naming conventions — wz_local suite

**Authoritative standard:** `WZ2/Standards/naming.md`
**Suite prefix:** `wz` — declared in `suite.json → "prefix"`
**App code (wztrack):** `wtrack` — declared in `suite.json → subprojects[].appcode`

This file is the suite-level binding. All rules come from `WZ2/Standards/naming.md`.
Only the prefix and appcode values are declared here — do not duplicate the rules.

---

## Derived names for wztrack

| Artefact | Pattern (from WZ2 standard) | Value |
|---|---|---|
| CSS file (global) | `{prefix}-{appcode}.css` | `wz-wtrack.css` |
| CSS file (page) | `{prefix}-{appcode}-{page}.css` | `wz-wtrack-kanban.css` |
| CSS class (app-specific) | `.{prefix}-{appcode}-*` | `.wz-wtrack-board-col` |
| CSS token | `--wz2-*` | `--wz2-accent` (workspace tokens, read-only) |
| localStorage token key | `{prefix}_{appcode}_token` | `wz_wtrack_token` |
| localStorage nav key | `{prefix}_{appcode}_nav_v{N}` | `wz_wtrack_nav_v1` |
| Window global | `window._{prefix}_{appcode}_{fn}` | `window._wz_wtrack_saveIssue` |
| Env var prefix | `{PREFIX}_{APPCODE}_` | `WZ_WTRACK_` |
| Python Settings prefix | `WZ_WTRACK_` | `WZ_WTRACK_DATABASE_URL` |
| DB schema | `{prefix}_{appcode}` | `wz_wtrack` |

## Hard rules (inherited from WZ2/Standards/naming.md)

1. Never hardcode a hex or rgba value — always use `var(--wz2-*)` tokens.
2. Never write a bare window global — always `window._wz_wtrack_{fn}`.
3. Never use a localStorage key without the `wz_` suite prefix.
4. Never write an env var without the `WZ_WTRACK_` prefix.
5. Never store output inside the project folder — output goes to `WZ2/Output/` or `WZ2/Research/`.
