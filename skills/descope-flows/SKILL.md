---
name: descope-flows
description: Build and validate Descope flows as raw flow JSON that imports as-is (console import or the Descope MCP ImportFlow). Use when the user asks for a Descope sign-up, sign-in, MFA, step-up, SSO, social login, OTP, magic link, passkey or progressive-profiling flow.
---

# Descope Flows

Write Descope flows as raw flow JSON: the same file the console's flow export produces and its import accepts. Start
from a recipe in this skill, change only what the user asked for, then validate before importing.

Read every skill file you use one file per call and to its last line. If a read comes back cut off (a truncation
note, a line or size limit), read the rest before you rely on the file; never work from the part you saw.

## Before building: settle these with the user

Ask in one short message, only what the request leaves open, and wait for the answers. Redoing a flow costs more.

- **Sign-up**: may new users sign up, or existing users only? With SSO, an existing-users-only flow must also stop a
  first SSO login from creating a user (`references/patterns.md`).
- **Security words**: what "lock", "block", "limit", "expire", "require" mean here: for how long, counted where
  (this attempt only, or across attempts), and how it ends (time, an admin, a reset). A count kept in the flow
  starts again with every new attempt: say so if the user expects more. Descope already caps wrong OTP codes at 3 per
  code (then the code is deleted; a resend starts over). A scriptlet counter can enforce a lower count within one
  run; a lock that outlives the run needs the app's backend. See `references/patterns.md`, "Lock after N wrong
  codes".
- **Failures on the auth path**: what happens when a connector, scriptlet or outside API fails or is down.
  Recommend failing closed (stop with a message) and never choose fail-open (continue without the check) silently:
  if the user picks it, name what it skips in the report.
- **Who may use it**: when the request names an audience ("our sales reps", "employees", "partners"), ask whether the
  flow must enforce it (email domain, tenant, role) or only describes it.
- **Account and SSO checks**: by default every unknown-account and wrong-credential failure gets one generic
  message ("If an account exists, we sent you a code", "Wrong email or password"). A message saying no account
  exists tells anyone which emails are registered: build it only if the user asks, and say so in the report. When
  the user types an email to find their SSO, ask whether the IdP's email must match it (`verifyInitiatedEmail` on
  `saml-start` and `exchange-saml-code`); recommend yes.
- **Values only they know**: thresholds, links, provider names, brand inputs. Values only their project holds
  (connector ids, site keys, redirect URLs) never hold up the build: take them if offered, otherwise keep the
  recipe's placeholder and list it in the report.
- **Migration from a legacy system**: is it checked on every sign-in (it still owns passwords), or only when
  Descope's own check fails (`references/patterns.md`)? Do password changes (reset, expiry, a change screen) belong
  in this flow or in a separate profile flow?
- **An outside API on the auth path**: how does it signal a wrong password or unknown user versus an outage (status
  codes, a body field)? The flow needs both to show the right message and to fail closed on outages.
- **Several tenants (companies, workspaces)**: which tenant does a new user join (none, one matched by email
  domain, a new one)? A user picks a tenant only after signing in: before sign-in the flow doesn't know the user's
  tenants. If the user wants the choice before sign-in, say this isn't supported and offer the closest supported
  shape (choose after sign-in, route by email domain, or have the app pass the tenant when it starts the flow).

When you offer a default answer, it must be something a recipe or `references/patterns.md` supports; otherwise say
it is unverified. Never default to skipping a security check: a step-up that skips re-verification ("signed in
within N minutes") needs a sign-in time the skill documents; without one, verify every time and say why.

## Workflow: build -> validate -> fix -> import

1. **Pick the closest recipe** in `recipes/README.md` and copy its `flow.json`. Never write a flow from scratch,
   by hand or by a script that generates tasks and screens: screens are large component trees that are easy to get
   subtly wrong. A script that copies recipes and edits the copy is fine if it keeps their task ids and screens
   (copy a screen with its ids; don't renumber it). No recipe fits? Check
   `references/patterns.md` (trusted device, existing users only, password migration, SSO enforcement, email or
   phone in one input), take the closest recipe, change it, and tell the user which parts are new and unverified.
   - **Keep everything the recipe does** unless the request explicitly changes it: its error routes, the expired
     password, locked account and reset paths, verified-email checks, name fields, legal links, email masking.
     "Only X", "then end" or "sign-in only" don't ask you to remove a path: ask the user before removing one, and
     keep it if you can't ask. The report lists every removal (step 7).
   - **Combining recipes**: the recipe closest to the main path is the base and keeps all its ids (tasks, screens,
     components, interactions). Each recipe you add parts from moves by one offset: its task ids become old +
     offset (`N.end` -> `(N+offset).end`), where the offset is the flow's highest numeric task id + 1 when you
     add it. Its screens keep their ids; a screen whose `screenId` is already in the flow gets new ids
     (`references/screens.md`). Note each recipe's offset: the diff in step 7 needs it.
2. **Adapt it** following `references/flow-structure.md`: tasks, screens, interactions and their ids must stay
   consistent with each other, and new tasks follow its "Make it look console-made" rules (ids, names, layout). Wire every requirement end to end: a value a screen collects is saved only if a task
   reads it (an action input of the same name, or `update-user-properties`), and every
   failure the user mentions (unknown email, wrong code, locked account) gets an explicit path and a message.
   Something asked for "after X" (after sign-in, after sign-up) goes on every path that does X: email, social, SSO,
   new and returning users alike.
   Fill in every value the flow needs (redirect URLs, terms and privacy links, connector ids, provider names): ask
   the user for the ones only they know, and set them in the flow yourself. Never hand back JSON with blanks for the
   user to edit, except values the user couldn't give you yet that only their project holds: a connector id or
   site key (the recipes' `REPLACE_WITH_...` placeholders), a redirect `uri` left empty. Keep the recipe's
   placeholder and list each one in the report with the task and argument to set. Terms and privacy links are the
   user's: ask for them, never make one up (`/terms`, `/privacy`); with no answer, keep the recipes'
   `REPLACE_WITH_TERMS_URL` and `REPLACE_WITH_PRIVACY_URL` hrefs and list them the same way. Never drop a trigger or step the user asked for because a value is unknown (a risk threshold, a
   limit): ask for it, or keep it with a value you chose and list that value under Assumed.
3. **Look up every action you add or change** and use its input names exactly; never guess one. With the Descope
   MCP connected, call `GetActionCatalog` with `query` (or `includeHidden: true` to browse: most actions flows run,
   like OTP and OAuth, are hidden from the unfiltered list; a call returns 25 actions, at most 50 with `limit`, so
   check `total` and narrow the query), then `full: true` for the actions you use. Without the
   MCP, read `references/catalog/README.md` in full first, then find the action in
   `references/catalog/actions/index.md` and read its group file (`actions/<group>.md`). There, inputs with Source
   `context` come from a screen input or context key of the same name and take no argument; inputs with Source
   `argument` go in `arguments`; the error ids listed are the only errors you can route.
4. **Validate.** Run `python3 scripts/validate_flow.py <flow.json>` (in this skill's folder, Python 3, no setup)
   and fix every error it reports; re-run until it prints no errors. Warnings are likely runtime problems: fix
   them or tell the user why not. Style notes only mean "doesn't look console-made": the flow imports and runs
   either way; fix them when it's cheap. It checks action ids, argument names, the task
   graph and the screens against this skill's catalog. Then, with the MCP, dry-run the import (exact call in
   `references/flow-structure.md`, "Validate and import with the MCP") and fix every diagnostic. The MCP checks
   less than the script: a clean dry run means the flow imports, not that it is right.
5. **Import.** With the MCP: apply the dry run's `draftToken` (`{draftToken, mode: "UPSERT"}`); send the raw
   `{flow}` only when the user wants an immediate overwrite. Without the MCP:
   the console's flow editor -> Import, or the Management API `POST /v2/mgmt/flow/import` with
   `{"flow": <file>}`. Import into a test project before production. Importing replaces a flow with the same id.
6. **Check it runs**: open the flow in the console editor and run it once (Run button, or the project's hosted login
   page with `?flow=<flowId>`).
7. **Report** in five sections, headed **Built**, **Changed from the recipe**, **Checked**, **Assumed, not
   verified** and **For review**, with no other sections except, when you couldn't import or run the flow (no MCP), a short **How to test** after
   them: the import steps from step 5 and the paths to try by hand, each with what should happen (a new user, a
   returning user, every failure path the user asked about).
   - **Built**: the tasks and routes, by path (screens, actions, conditions, where each error goes). Only what the
     JSON shows: never that a path works, signs in, blocks or stores something. What a task does at runtime beyond
     its catalog description (creates a user, sends, stores) goes under Assumed with its source.
   - **Changed from the recipe**: run `python3 scripts/recipe_diff.py <flow.json> --recipe
     recipes/<base>/flow.json` on the final file, adding `--recipe recipes/<other>/flow.json@<offset>` for every
     other recipe you took parts from, and quote its output as printed: removals first. After each removal say
     why: the user asked, or agreed when you asked. A removal with neither goes back into the flow. Also name
     behavior the recipe brings that the user didn't ask for (an existing session skipping verification, an
     optional field), so they can say whether to keep it. Never skip this section or replace it with `diff --stat`
     or a summary of your own.
   - **Checked**: only what you ran in this session, with its result (validate_flow.py, the dry run, an import, a
     console run). Count runs from your own commands, not from memory: "validate_flow.py: 3 runs, the last clean".
     Anything you didn't run, say so: "not imported", "not run". A recipe README's "Checked" is about the recipe,
     not your flow: never report it as your check.
   - **Assumed, not verified**: every runtime behavior the JSON doesn't show (errors an action raises, timeouts,
     defaults such as sender, code length, score scales and thresholds, what the app or IdP receives), each with
     its source: a skill file, the catalog, a Descope docs page (with its URL), or your general knowledge.
     Advice on what the user's app or IdP must do belongs here too, unless a skill file says it.
   - **For review**: a checklist the user can hand to someone who reviews the flow: the parts generated rather
     than copied from a recipe (the diff's Added lines, with their task and screen ids); every security choice (fail closed or open,
     generic or explicit account messages, SSO email binding, any skipped verification, who may sign in); every
     placeholder to fill; and every requirement not run end to end, each with the path to try.
   Under Built, name any path that skips an "after X" step, and why.
   Never state a number, default or platform behavior as fact unless a skill file or your own check says it. Say a
   value is stored only when a task writes it. Limits are claims too: never write that something can't be done,
   isn't possible, or works only one way unless a skill file says so; say the skill has no reference for it and
   ask, or try it and check. When you restate a condition from a skill file, keep its scope: copy its wording and
   don't add "only" or "always".

## References

- `references/flow-structure.md` - the flow JSON anatomy: envelope, tasks, rules, conditions, screens, ids
- `references/screens.md` - writing screens: component tree, what submits a screen, inputs, ids
- `references/guardrails.md` - mistakes that pass validation but break at runtime; read before importing
- `references/patterns.md` - common requests without a recipe: how to wire them from the closest one
- `references/connectors.md` - connector tasks (Generic HTTP, reCAPTCHA, fraud checks): arguments, results, failures
- `references/catalog/README.md` - every action (inputs, outcomes, errors), condition operator and screen component,
  generated from the backend code
- `recipes/README.md` - index of complete flows that import as-is; each recipe folder has `flow.json` and a README
  saying what to change

## DO NOT

- DO NOT invent action ids or argument names: look them up (`GetActionCatalog`) or copy them from a recipe
- DO NOT enable auth methods or import a project snapshot to "make a flow work": flows don't need the method switched on
  (`references/guardrails.md`)
- DO NOT import a flow `scripts/validate_flow.py` reports errors for, and don't trust a clean MCP dry run or
  `ValidateFlow` alone: neither checks arguments against the catalog
- DO NOT drop the `view` positions or rename task ids: console import lays the flow out from `view`, and the MCP
  import gives any id that isn't numeric (or `N.end`, `start`) a new number
- DO NOT hardcode secrets (API keys, client secrets) in flow JSON: use connectors and project settings
