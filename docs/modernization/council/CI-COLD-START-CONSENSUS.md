# Byzantine Consensus — CI cold-start on fork `prondubuisi/mezzanine`

| Field | Value |
|---|---|
| **Incident** | GitHub Actions never registered or ran on the Nova fork; PR #14 had empty `statusCheckRollup` |
| **Session** | Prior: `019ff526-e17d-7f31-ac1b-1b6850458254` (false-green on `pr-14:ci-green`). This council: 2026-08-12 |
| **Repo** | `prondubuisi/mezzanine` (fork of `stephenmcd/mezzanine`), branch `nova/16-wp-importer`, PR #14 |
| **Date** | 2026-08-12 |
| **Status** | **Binding.** Root cause proven; registration fix applied and verified |

---

## Evidence (pre-fix)

| Probe | Result |
|---|---|
| `GET /repos/prondubuisi/mezzanine/actions/workflows` | `{"total_count":0,"workflows":[]}` |
| `gh run list` | empty |
| PR #14 `statusCheckRollup` | `[]` |
| Check-suites for master HEAD `85dfd412` | `total_count: 0` |
| Check-suites for feature HEAD `59c4ece6` | `total_count: 0` |
| `GET .../actions/permissions` | `enabled: true`, `allowed_actions: all` |
| `GET .../actions/permissions/workflow` | `default_workflow_permissions: write` |
| Contents API: `.github/workflows/main.yml` on `master` | present (legacy matrix, sha `1566688…`) |
| Feature `.github/workflows/main.yml` | modern py312–314 × dj52/60/61 + lint + audit + `workflow_dispatch` |
| Parent `stephenmcd/mezzanine` workflows | `total_count: 1`, recent successful runs |
| Fork metadata | `fork: true`, created `2026-08-11T13:51:15Z`, default branch `master` |
| Auth scopes | `repo`, `workflow` present |
| `gh workflow run "Test and release"` | "could not find any workflows" |
| `POST .../workflows/main.yml/dispatches` (pre-reg) | fails (no registered workflow) |

**Local pytest green and Friday-path fixes are real but orthogonal.** They are not an external CI signal.

---

## Root cause (binding diagnosis)

**Fork Actions cold-start / registration lag, not a missing YAML file and not Settings→Actions permissions alone.**

1. Workflow files existed on the default branch (`master`) and on `nova/16-wp-importer`.
2. Repository Actions *permissions* were already enabled (`enabled: true`, `allowed_actions: all`).
3. Despite (1)+(2), the Actions **workflow registry** was empty (`total_count: 0`). No workflow IDs, no runs, no check-suites — so `workflow_dispatch`, PR checks, and badges could not exist.
4. This matches known GitHub behavior for forks / cloned-with-workflows repos: permissions can read “on” while the Actions service has never **indexed** workflow paths into the per-repo workflow catalog. Community reports (e.g. [discussion #25219](https://github.com/orgs/community/discussions/25219), [discussion #29029](https://github.com/orgs/community/discussions/29029), [discussion #50736](https://github.com/orgs/community/discussions/50736), [discussion #104281](https://github.com/orgs/community/discussions/104281)) describe: empty Actions sidebar, “I understand my workflows, enable them” banner, rename/re-commit workarounds, and **no first-class API for the banner** beyond permissions toggles.
5. **Proven fix:** `PUT /repos/.../actions/permissions` with `{"enabled": false}` then again with `{"enabled": true, "allowed_actions": "all"}` caused GitHub to index the default-branch workflow within seconds:
   - After cycle: `total_count: 1`, workflow id `332672233`, name `Test and release`, path `.github/workflows/main.yml`, `state: active`, `created_at: 2026-08-12T11:47:53+01:00`.
6. **Trigger after registration:** empty commit on `nova/16-wp-importer` produced real runs (`push` + `pull_request`) and non-empty PR check rollup (modern matrix jobs: `test (py312-dj52, …)`, lint, pip-audit, …).
7. **Secondary truth:** master’s registered workflow still lacks `workflow_dispatch` (legacy `on: pull_request, push` only). Feature branch has `workflow_dispatch`, but dispatch-by-API still keys off the **default-branch** definition of that workflow path. That is why post-registration `dispatches` returned `422 Workflow does not have 'workflow_dispatch' trigger` against `master`’s YAML — expected, not a remaining registration failure.

**Not the root cause (ruled out):** billing lockout (no evidence; runs queue after re-index), invalid YAML (file served and then executed), path filters, private-repo fork PR approval gates (same-fork PR), missing `workflow` OAuth scope, parent-repo disable, or “workflow only on feature branch” (file was already on `master`).

**Process failure (prior session):** marking `pr-14:ci-green` complete without `actions/workflows` non-empty and without a run ID is a **false green** — category error against PLATFORM honesty and SKEPTIC vetoes.

---

## Motions

| ID | Motion |
|---|---|
| **C1** | Root cause is fork Actions registry cold-start / missing index, not product code |
| **C2** | Durable fix = re-index via permissions disable→enable (or equivalent UI enable banner), then push/PR event — not claim local pytest as CI green |
| **C3** | Prefer least invasive path: no default-branch product rewrite, no force-push; empty commit on feature after re-index is enough to light PR #14 |
| **C4** | Never mark CI green without external (or explicitly labeled local-substitute) evidence; prior false-green is repudiated |
| **C5** | Security gates (lint, pip-audit, living matrix) stay; do not weaken to force a green |
| **C6** | Optional follow-up: put modern workflow + `workflow_dispatch` on `master` via a tiny bootstrap PR so dispatch and default-branch CI match Nova — **not** required to unblock PR #14 once registered |
| **C7** | If GitHub re-enters `total_count: 0`, re-run permissions cycle; if that fails, honest local tox matrix + BLOCKED human steps — never confabulate |

---

## Independent general votes

### PLATFORM (CI / DevEx honesty) — `07-platform.md`

| Motion | Vote | Note |
|---|---|---|
| C1 | **YES** | Registry empty while file present is a platform/index bug class, not tox |
| C2 | **YES** | Living matrix is useless if Actions never indexes; re-index is the job |
| C3 | **YES** | Minimal blast radius; do not burn minutes on master’s EOL dj22 matrix unless needed |
| C4 | **YES** | Platform reboot requires honest CI; local green ≠ shipped green |
| C5 | **YES** | Keep audit + lint + matrix |
| C6 | **YES (follow-up)** | Bootstrap master when product history allows; not a blocker once PR runs |
| C7 | **YES** | Document the recovery spell |

**PLATFORM synthesis:** Registration is a platform primitive. Ship the recovery procedure in council docs. Prefer API-reproducible fix over folklore UI clicks when both work.

### SKEPTIC — `14-skeptic.md`

| Motion | Vote | Note |
|---|---|---|
| C1 | **YES** | Evidence table is the only acceptable narrative |
| C2 | **YES** | |
| C3 | **YES** | Refuse theater commits that rewrite product story |
| C4 | **YES — binding veto on false green** | Prior session’s `ci-green` is void |
| C5 | **YES** | Do not drop pip-audit to “pass” |
| C6 | **ABSTAIN / later** | Only if it does not fake product readiness |
| C7 | **YES** | BLOCKED with human steps beats fiction |

**SKEPTIC synthesis:** “CI green” requires a run URL and a conclusion, or an explicit `LOCAL-ONLY` label. No third state.

### PRODUCT — `13-product.md`

| Motion | Vote | Note |
|---|---|---|
| C1–C4 | **YES** | Cannot claim Friday path or PR merge readiness without checks |
| C5 | **YES** | Security is product default |
| C6 | **YES** | Bootstrap PR is good DevEx for the fork as a working product surface |
| C7 | **YES** | |

### WORDPRESS — `10-wordpress.md`

| Motion | Vote | Note |
|---|---|---|
| C1–C5 | **YES** | WP migrate ability still ships on kits wedge; CI is the gate for importer PR #14 |
| C6 | **YES** | Unblocks iterating importer under real checks |
| C7 | **YES** | |

### SECURITY — `04-security.md`

| Motion | Vote | Note |
|---|---|---|
| C1 | **YES** | |
| C2 | **YES** | Re-enable Actions is not a privilege escalation if already admin |
| C3 | **YES** | Avoid force-push / history rewrite |
| C4 | **YES** | False green is a security process failure |
| C5 | **YES — hard** | Keep `pip-audit`, lint, matrix; no “skip on fork” holes |
| C6 | **CAUTION** | Master bootstrap must not reintroduce secret-exfiltrating release jobs on the fork without owner guards (release already gated `repository_owner == 'stephenmcd'`) |
| C7 | **YES** | |

### LEGACY — `08-legacy.md`

| Motion | Vote | Note |
|---|---|---|
| C1 | **YES** | Fork inherits upstream workflow path; registry does not auto-activate |
| C2 | **YES** | |
| C3 | **YES** | Do not thrash `master` legacy matrix unless registration demands a file change (it did not) |
| C4 | **YES** | |
| C5 | **YES** | |
| C6 | **YES with care** | Replacing master matrix is a product cutover (Nova platform reboot), not an incident patch; separate PR |
| C7 | **YES** | |

### ARCHITECT — `01-architect.md` / vote-G

| Motion | Vote | Note |
|---|---|---|
| C1 | **YES** | Diagnosis is environmental, fix is operational |
| C2 | **YES** | Durable enough: permissions cycle is idempotent and documented |
| C3 | **YES** | Least invasive: toggle + empty commit beats default-branch rewrite |
| C4 | **YES** | |
| C5 | **YES** | Gates are architecture |
| C6 | **DEFER** | Master modern workflow is Wave platform work; not required for this incident’s definition of done |
| C7 | **YES** | |

### INTERFACE / EDITOR

Not material to CI registration. No vote required. Recorded as **N/A**.

---

## Tally

| Motion | PLATFORM | SKEPTIC | PRODUCT | WORDPRESS | SECURITY | LEGACY | ARCHITECT | Result |
|---|---|---|---|---|---|---|---|---|
| C1 Root cause = registry cold-start | Y | Y | Y | Y | Y | Y | Y | **Y 7/7** |
| C2 Fix = re-index + real event | Y | Y | Y | Y | Y | Y | Y | **Y 7/7** |
| C3 Least invasive (no master rewrite) | Y | Y | Y | Y | Y | Y | Y | **Y 7/7** |
| C4 No false green | Y | Y | Y | Y | Y | Y | Y | **Y 7/7** |
| C5 Do not weaken gates | Y | Y | Y | Y | Y | Y | Y | **Y 7/7** |
| C6 Master bootstrap modern workflow | Y | later | Y | Y | caution | care | defer | **Optional follow-up** (not incident DOD) |
| C7 Honest BLOCKED fallback | Y | Y | Y | Y | Y | Y | Y | **Y 7/7** |

### Unanimous refusals (this incident)

- Do not mark `ci-green` from local pytest alone.
- Do not disable `pip-audit` / lint / matrix to manufacture a pass.
- Do not force-push or rewrite product history on `master` for this incident.
- Do not claim “GitHub is fine” while `actions/workflows.total_count == 0`.

---

## Binding synthesis

1. **Root cause accepted (C1):** GitHub Actions on this public fork never indexed workflows into the Actions catalog despite files on `master` and Actions permissions enabled. That is a fork cold-start / registry state, not a Nova code defect.
2. **Primary workaround accepted (C2+C3):**  
   ```bash
   # Re-index (idempotent recovery)
   gh api -X PUT repos/prondubuisi/mezzanine/actions/permissions --input - <<'EOF'
   {"enabled": false}
   EOF
   gh api -X PUT repos/prondubuisi/mezzanine/actions/permissions --input - <<'EOF'
   {"enabled": true, "allowed_actions": "all"}
   EOF
   # Confirm registry
   gh api repos/prondubuisi/mezzanine/actions/workflows --jq .total_count   # expect >= 1
   # Fire an event (push or empty commit on the PR branch)
   git commit --allow-empty -m "ci: trigger Actions after registry re-index"
   git push
   ```
3. **Honesty gate (C4):** External CI status is **FIXED** only when (a) `workflows.total_count >= 1`, (b) at least one `workflow_runs` row exists for the PR head, (c) PR `statusCheckRollup` is non-empty. Job **conclusions** may still fail for product reasons — that is a separate green/red, not “no CI.”
4. **Gates stay (C5).**
5. **Master modernisation (C6)** is a follow-up PR, not required to close this incident.
6. **If registration regresses (C7):** re-run the cycle; if still zero, leave status **BLOCKED** with human UI path: Actions tab → “I understand my workflows, enable them” → push; optional rename of workflow file on default branch (community workaround).

---

## What was executed (this session)

| Step | Action | Result |
|---|---|---|
| 1 | Full diagnostic (API, permissions, contents, check-suites, parent comparison) | `total_count: 0` confirmed |
| 2 | Online research (fork enable, dispatch default-branch, rename bugs) | Aligns with registry cold-start |
| 3 | `PUT` permissions disable → enable | Workflow `332672233` registered, `state: active` |
| 4 | Empty commit `995e14e7` on `nova/16-wp-importer` + push | Runs `31589048198` (push) and `31589048926` (pull_request) **queued/in_progress** |
| 5 | PR #14 check rollup | Real checks: modern matrix + lint + pip-audit |
| 6 | This consensus file | Written under `docs/modernization/council/` |

---

## Verification commands (re-run anytime)

```bash
gh api repos/prondubuisi/mezzanine/actions/workflows --jq '{total_count, workflows: [.workflows[]|{name,path,state,id}]}'
gh api repos/prondubuisi/mezzanine/actions/runs --jq '{total_count, recent: [.workflow_runs[:3][]|{id,event,status,conclusion,head_branch,html_url}]}'
gh pr view 14 --json statusCheckRollup --jq '.statusCheckRollup | length'
```

---

## Residual / follow-ups (not blockers for “CI registered”)

| Item | Owner | Notes |
|---|---|---|
| **lint job FAILURE** | Product follow-up | External CI ran and reported honestly: full living matrix **success**, `pip-audit` **success**, `lint` **failure** — ruff `I001` import sort (11 errors, 7 auto-fixable). Example: `tests/test_sanitize.py`, preview tests. **Not** a registration issue. |
| `workflow_dispatch` on default branch | Optional bootstrap PR | Master YAML lacks dispatch; feature has it — `POST .../dispatches` → 422 until master YAML gains the trigger |
| `publish.yml` only on feature | Optional | Registers when present on default branch |
| Replace master legacy dj22 matrix with Nova matrix | Platform reboot PR | Separate from cold-start; avoid running EOL matrix for fun |
| Prior session false-green | Process | Repudiated by C4 |

### Post-fix verification (runs completed)

```text
workflows.total_count = 1  (id 332672233, active)
workflow_runs.total_count = 4+
PR #14 statusCheckRollup length = 27 (non-empty)
Run 31589048926 (PR, 995e14e7): conclusion=failure
  test py312–314 × dj52/60/61: all success
  pip-audit: success
  lint: failure (ruff I001)
  release/docs: skipped (expected on fork / non-stable)
Run 31589148171 (PR, d7cbe23d consensus commit): same shape — lint fail only
```

---

## Honest CI status (binding at time of writing)

| Layer | Status |
|---|---|
| **Actions registration** | **FIXED** (`total_count: 1`, workflow active) |
| **Runs exist for PR branch** | **FIXED** (push + pull_request run IDs; conclusions recorded) |
| **PR #14 checks visible** | **FIXED** (non-empty rollup, modern job names) |
| **All jobs conclusion=success** | **NO** — lint fails (ruff I001); matrix + audit green |
| **Overall incident (never registered)** | **FIXED** |
| **Overall “CI green for merge”** | **PARTIAL** — real external red on lint; do **not** claim merge-green |

---

## Alignment with standing CONSENSUS / DESIGN

- **M1 C / platform reboot:** living matrix only matters if it runs externally.
- **M4 B kits + Friday wedge; WP migrate as ability:** PR #14 is that ability; it needs real checks.
- **Unanimous refusals:** no category error; no false product claims — extended here to **no false CI claims**.
