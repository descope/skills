#!/usr/bin/env python3
"""Check a Descope flow JSON file before importing it. Python 3 standard library only, no network.

    python3 validate_flow.py <flow.json> [--json]

Exit 0 when the flow has no errors, 1 when it has, 2 when the file can't be read or isn't JSON.
Fix every error; warnings are worth reading; info lines are things to double-check. --json prints
{"ok", "errors": [{"code", "path", "message", "taskId"?}], "warnings": [...], "info": [...], "style": [...]}.

What it checks (the action catalog is ../references/catalog/actions.json):
- the file's shape: an ExportedFlow {flowId, metadata{name}, contents{startTask, tasks}, screens}, optionally
  wrapped in {"flow": ...};
- what Descope's import rejects: startTask, next rules to missing tasks, condition operators and branches;
- what import accepts but breaks at runtime: unknown actions, argument names the action doesn't have, missing
  required inputs, argument types other than inline/context, step ids (exchangeStepId, verifyStepId,
  finishStepId) naming no task, subflows without arguments.flowId, group actions used as tasks, "new-" screen
  ids, empty dynamic values;
- warnings for a password flow that dropped what the password recipes handle: the PasswordExpired route, the
  forgot-password path, the verified-email check after a password sign-up;
- notes (info) for an action before any screen whose errors fall to automatic handling (the flow fails there) and
  for a flow that shares no screen or condition id with any recipe (likely written from scratch);
- screens (flow_screens.py, when present) and console likeness (flow_style.py, reported as "style").

Error codes match Descope's ValidateFlow (E1041xx), and the checks mirror the ones it runs.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # importing flow_screens/flow_style must not write into the skill folder

HERE = Path(__file__).resolve().parent
CATALOG = HERE.parent / "references" / "catalog" / "actions.json"
CONTEXT_KEYS = HERE.parent / "references" / "catalog" / "context-keys.json"
RECIPES = HERE.parent / "recipes"
# Condition keys the reference can't list: form fields, step outputs, lists, claims, cookies, custom attributes.
DYNAMIC_KEY_PREFIXES = ("form.", "connectors.", "scripts.", "scriptlets.", "lists.", "jwtClaims.", "cookies.",
                        "user.customAttributes.", "tenant.customAttributes.", "jq:")
# Namespaces that mirror user.* (unauthUser before sign-in, authInfo.user after).
USER_MIRRORS = ("unauthUser.", "authInfo.user.")

TASK_TYPES = {"screen", "automated", "condition", "flow"}
TASK_FIELDS = {
    "id", "name", "next", "type", "action", "arguments", "screenId", "contextKeys", "inputKeys", "allInputKeys",
    "dynamicSelects", "calculatedInputKeys", "clientScripts", "componentsConnectors", "connectorComponentProps",
    "recoveryCodesData", "conditions", "clientCondition", "clientConditions", "componentsConditions", "view", "note",
    "errorHandlingV2",
    # Read by the importer under its legacy name, and editor leftovers the import drops harmlessly.
    "errorHandling", "inputsMetadata", "htmlTemplate", "interactions", "failFlowOnError",
}
ROW_TYPES = {"string", "number", "boolean", "context", "object", "array"}
# Object inputs the action decodes into a list of {key, type, value} rows.
ROW_LIST_INPUTS = {("scriptlet", "overrideForm")}
STEP_ID_INPUTS = {"exchangeStepId", "verifyStepId", "finishStepId"}
DEFAULT_OAUTH_PROVIDERS = {"google"}
# Missing required inputs with a working runtime fallback: None drops the finding, "warning" downgrades it.
REQUIRED_INPUT_SEVERITY = {
    ("connector", "exchangeStepId"): None,
    ("update-user-properties", "userPropertiesDefinitions"): "warning",
}
SCREEN_ID_RE = re.compile(r"^[A-Za-z0-9_-]*$")
# Listed in the catalog but with no executor: the server fails when a flow reaches them (checked end to end).
NOT_RUNNABLE = {"sign-in-totp": "verify-totp-code"}

# Codes, as Descope's ValidateFlow reports them.
INVALID_ACTION = "E102101"
INVALID_NEXT_TASK = "E104101"
INVALID_START_TASK = "E104102"
EMPTY_CONDITIONS = "E104103"
UNKNOWN_OPERATOR = "E104104"
EMPTY_RULE_INTERACTION = "E104105"
EMPTY_RULE_TASK = "E104106"
EMPTY_CONDITION_INTERACTION = "E104107"
INVALID_SCREEN_ID = "E104112"
NIL_TASK = "E104113"
TASK_MISSING_NAME = "E104114"
EMPTY_DYNAMIC_VALUE = "E104115"
UNKNOWN_ARGUMENT = "E104117"
MISSING_REQUIRED_ARGUMENT = "E104118"
INVALID_ARGUMENT_TYPE = "E104119"
INVALID_STEP_REFERENCE = "E104120"
MISSING_SUBFLOW_ID = "E104121"
UNKNOWN_TASK_FIELD = "E104122"
OAUTH_PROVIDER_NOT_DEFAULT = "E104123"


class Report:
    def __init__(self):
        self.errors, self.warnings, self.info = [], [], []

    def add(self, code, path, message, task_id=None, severity="error"):
        item = {"code": code, "path": path, "message": message}
        if task_id is not None:
            item["taskId"] = task_id
        {"warning": self.warnings, "info": self.info}.get(severity, self.errors).append(item)


def load_context_keys():
    try:
        data = json.loads(CONTEXT_KEYS.read_text())
    except (OSError, ValueError):
        return {}
    return {k["key"]: k for section in data.get("sections") or [] for k in section.get("keys") or []
            if isinstance(k, dict) and k.get("key")}


def check_condition_keys(tasks, conditions, keys, report):
    """Checks condition targets against the context-keys reference and operators against the key's type. Keys are
    case-sensitive context paths. A user.* key not in the reference, or a listed key the engine doesn't load on its
    own ("Don't use" in the reference), is a warning; an unlisted key in another namespace the reference covers is
    only info, since the reference can't list every path."""
    if not keys:
        return
    namespaces = {k.split(".")[0] for k in keys}
    for task_id in sorted(tasks):
        task = tasks[task_id]
        if not isinstance(task, dict) or task.get("type") != "condition":
            continue
        for i, branch in enumerate(task.get("conditions") if isinstance(task.get("conditions"), list) else []):
            atoms = branch.get("atomicConditions") if isinstance(branch, dict) else None
            for j, atom in enumerate(atoms if isinstance(atoms, list) else []):
                target = atom.get("target") if isinstance(atom, dict) else None
                key = target.get("value") if isinstance(target, dict) and target.get("type") == "context" else None
                if not isinstance(key, str) or key.startswith(DYNAMIC_KEY_PREFIXES):
                    continue
                path = f"$.tasks.{task_id}.conditions[{i}].atomicConditions[{j}]"
                lookup = next(("user." + key[len(m):] for m in USER_MIRRORS if key.startswith(m)), key)
                spec = keys.get(key) or keys.get(lookup)
                if spec is None:
                    if lookup.startswith("user.") and not any(lookup.startswith(k + ".") for k in keys):
                        known = list(keys)
                        close = [k for k in known if k.lower() == lookup.lower()] or difflib.get_close_matches(
                            lookup, known, n=1)
                        hint = f"; did you mean {close[0]!r}?" if close else ""
                        report.add("condition_key_unknown", f"{path}.target.value",
                                   f"Context key {key!r} is not in references/catalog/context-keys.md, so it may not "
                                   f"resolve (keys are case-sensitive)"
                                   f"{hint}", task_id, "warning")
                    elif (not lookup.startswith("user.") and lookup.split(".")[0] in namespaces
                          and not any(lookup.startswith(k + ".") for k in keys)):
                        report.add("condition_key_unknown", f"{path}.target.value",
                                   f"Context key {key!r} is not in references/catalog/context-keys.md; it resolves "
                                   "only if that path exists in the flow's context (keys are case-sensitive).",
                                   task_id, "info")
                    continue
                if str(spec.get("description", "")).startswith("Don't use"):
                    report.add("condition_key_not_loaded", f"{path}.target.value",
                               f"Context key {key!r}: {spec['description']}", task_id, "warning")
                applicable = (conditions.get(atom.get("operator")) or {}).get("applicableOn")
                if applicable and spec.get("type") and spec["type"] not in applicable:
                    report.add("condition_type_mismatch", f"{path}.operator",
                               f"Operator {atom.get('operator')!r} applies to {', '.join(applicable)}, but {key} is a "
                               f"{spec['type']}.", task_id, "warning")


def load_catalog():
    data = json.loads(CATALOG.read_text())
    return data.get("actions") or {}, data.get("conditions") or {}


def unwrap(data, report):
    """Returns (exported_flow or None, dsl). Reports shape problems."""
    flow = data["flow"] if isinstance(data.get("flow"), dict) else data
    if flow is not data and isinstance(flow.get("dsl"), dict):
        report.add("shape_legacy_export", "$.flow.dsl",
                   "Legacy export {flow: {dsl}, screens} imports only through a deprecated endpoint. "
                   "Write an ExportedFlow {flowId, metadata, contents, screens}.")
        return None, flow["dsl"]
    if not isinstance(flow.get("contents"), dict):
        report.add("shape_bare_dsl", "$",
                   "A bare flow DSL is not importable as is. Wrap it in an ExportedFlow "
                   "{flowId, metadata, contents, screens}.", severity="warning")
        dsl = flow.get("dsl") if isinstance(flow.get("dsl"), dict) else flow
        return None, dsl
    metadata = flow.get("metadata")
    if not isinstance(metadata, dict):
        report.add("metadata_missing", "$.metadata", "metadata is required: import fails with E011003.")
    elif not metadata.get("name"):
        report.add("metadata_name_missing", "$.metadata.name", "metadata.name is required: import fails with E011003.")
    flow_id = flow.get("flowId")
    if not flow_id:
        report.add("flow_id_missing", "$.flowId",
                   "flowId is missing: the mgmt API and the MCP need it inside the flow.", severity="warning")
    elif not isinstance(flow_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", flow_id):
        report.add("flow_id_format", "$.flowId", f"flowId {flow_id!r}: use lowercase letters, digits and '-'.",
                   severity="warning")
    return flow, flow["contents"]


def check_dsl(dsl, actions, conditions, report, shared=()):
    tasks = dsl.get("tasks")
    if tasks is None:
        tasks = {}
    if not isinstance(tasks, dict):
        report.add("E011001", "$.tasks", "tasks must be an object of task id -> task.")
        return
    start = dsl.get("startTask")
    entry = tasks.get(start) if isinstance(start, str) else None
    if not tasks:
        if not start:
            report.add(INVALID_START_TASK, "$.startTask", "Start task is empty.")
        return
    if not isinstance(entry, dict):
        report.add(INVALID_START_TASK, "$.startTask", f"Start task {start!r} is not a task in this flow.")
    elif entry.get("type") not in TASK_TYPES:
        report.add(INVALID_START_TASK, f"$.tasks.{start}.type",
                   f"Start task {start!r} has type {entry.get('type')!r}; point startTask at the first real task "
                   "(screen, automated, condition or flow), not at the typeless start node.", start)

    groups = {}
    for group_id, group in actions.items():
        for member in group.get("members") or []:
            groups.setdefault(member, []).append(group)

    for task_id in sorted(tasks):
        task = tasks[task_id]
        path = f"$.tasks.{task_id}"
        if task is None:
            report.add(NIL_TASK, path, "Task is null.", task_id)
            continue
        if not isinstance(task, dict):
            report.add("E011001", path, "Task must be an object.", task_id)
            continue
        if check_field_types(task_id, task, path, report):
            continue
        for key in sorted(task):
            if not any(key.lower() == f.lower() for f in TASK_FIELDS):
                report.add(UNKNOWN_TASK_FIELD, f"{path}.{key}",
                           f"Task field {key!r} is not part of the task format and is dropped on import"
                           + ("; a subflow's id goes in arguments.flowId." if key == "flowId" else "."),
                           task_id, "warning")
        if not task.get("name"):
            report.add(TASK_MISSING_NAME, f"{path}.name", "Task has no name.", task_id, "warning")
        check_validator_rules(tasks, task_id, task, path, conditions, report)
        arguments = task.get("arguments") if isinstance(task.get("arguments"), dict) else {}
        check_empty_dynamic(task_id, arguments, report)
        task_type = task.get("type")
        if task_type == "flow":
            flow_id = arguments.get("flowId")
            if not (isinstance(flow_id, dict) and flow_id.get("type") == "inline" and flow_id.get("value")):
                report.add(MISSING_SUBFLOW_ID, f"{path}.arguments.flowId",
                           'Subflow task needs the child flow id as arguments.flowId: {"type": "inline", "value": '
                           '"<flow id>"}; a top-level flowId is dropped on import.', task_id)
        if task_type == "screen":
            screen_id = task.get("screenId") or ""
            # Import swaps "new-X" for a fresh id on task X only; on any other task the screen is dropped.
            if isinstance(screen_id, str) and screen_id.startswith("new-") and screen_id[4:] != task_id:
                report.add(INVALID_SCREEN_ID, f"{path}.screenId",
                           f"Screen id {screen_id!r} starts with 'new-', which import treats as an unsaved editor "
                           "screen and drops; choose another id.", task_id)
        if task_type == "automated" and task.get("action"):
            check_action(tasks, task_id, task, path, arguments, actions, groups, report)
            check_success_route(task_id, task, path, actions, shared, report)


# JSON types of the task fields the importer decodes strictly (Go domain.Task): a value of another type fails
# the whole import ("cannot unmarshal ...").
STR, LIST, OBJ, BOOL, NUM = str, list, dict, bool, (int, float)
TASK_FIELD_TYPES = {
    "id": STR, "name": STR, "type": STR, "action": STR, "screenId": STR, "arguments": OBJ, "next": OBJ,
    "conditions": LIST, "contextKeys": LIST, "inputKeys": LIST, "allInputKeys": LIST, "calculatedInputKeys": BOOL,
    "clientScripts": LIST, "clientConditions": LIST, "componentsConditions": LIST, "view": OBJ, "note": OBJ,
    "errorHandlingV2": OBJ, "errorHandling": OBJ, "dynamicSelects": OBJ, "componentsConnectors": OBJ,
    "connectorComponentProps": OBJ, "recoveryCodesData": LIST,
}


def check_field_types(task_id, task, path, report):
    """Reports values of the wrong JSON type; returns True when the task can't be checked further."""
    problems = []
    for key, value in task.items():
        expected = next((t for f, t in TASK_FIELD_TYPES.items() if f.lower() == key.lower()), None)
        if expected is None or value is None:
            continue
        if not isinstance(value, expected) or (expected is NUM and isinstance(value, bool)):
            problems.append((key, value))
    next_ = task.get("next")
    if isinstance(next_, dict):
        rules = next_.get("rules")
        if rules is not None and (not isinstance(rules, list) or not all(
                isinstance(r, dict) and all(isinstance(r.get(k, ""), str) for k in ("interactionId", "taskId"))
                for r in rules)):
            problems.append(("next.rules", rules))
    for name, arg in (task.get("arguments") or {}).items() if isinstance(task.get("arguments"), dict) else []:
        if arg is not None and (not isinstance(arg, dict) or not isinstance(arg.get("type", ""), str)):
            problems.append((f"arguments.{name}", arg))
    if isinstance(task.get("errorHandling"), dict):
        for err_type, handling in task["errorHandling"].items():
            if not isinstance(handling, str):
                problems.append((f"errorHandling.{err_type}", handling))
    for key, value in problems:
        report.add("E011004", f"{path}.{key}",
                   f"Task field {key} has the wrong JSON type ({type(value).__name__}); Descope's import rejects the "
                   "whole flow.", task_id)
    return bool(problems)


def check_validator_rules(tasks, task_id, task, path, conditions, report):
    """The checks Descope's import runs (ValidateFlow): it stops at the first
    problem in a task, and checks every next rule's target."""
    task_type = task.get("type")
    next_ = task.get("next") if isinstance(task.get("next"), dict) else {}
    rules = [r for r in next_.get("rules") or [] if isinstance(r, dict)]
    first = None
    if task_type == "condition":
        branches = task.get("conditions") if isinstance(task.get("conditions"), list) else []
        if not branches:
            first = (EMPTY_CONDITIONS, f"{path}.conditions", "Condition task has no conditions.")
        for i, branch in enumerate(branches):
            if first:
                break
            branch = branch if isinstance(branch, dict) else {}
            if not branch.get("interactionId"):
                first = (EMPTY_CONDITION_INTERACTION, f"{path}.conditions[{i}].interactionId",
                         "Condition has no interactionId.")
            elif not branch.get("atomicConditions") and branch.get("interactionId") != "ELSE":
                first = (EMPTY_CONDITIONS, f"{path}.conditions[{i}].atomicConditions",
                         "Condition has no atomicConditions (only ELSE may have none).")
            else:
                for j, atom in enumerate(branch.get("atomicConditions") or []):
                    operator = atom.get("operator") if isinstance(atom, dict) else None
                    if conditions and operator not in conditions:
                        first = (UNKNOWN_OPERATOR, f"{path}.conditions[{i}].atomicConditions[{j}].operator",
                                 f"Unknown condition operator {operator!r}; see references/catalog/conditions.md.")
                        break
    if task_type == "screen" and not first:
        screen_id = task.get("screenId") or ""
        if not isinstance(screen_id, str) or not SCREEN_ID_RE.match(screen_id):
            first = (INVALID_SCREEN_ID, f"{path}.screenId",
                     f"Screen id {screen_id!r}: use only letters, digits, '-' and '_'.")
    if task_type in ("automated", "screen") and not first:
        for i, rule in enumerate(rules):
            if not rule.get("interactionId"):
                first = (EMPTY_RULE_INTERACTION, f"{path}.next.rules[{i}].interactionId", "Next rule has no interactionId.")
            elif not rule.get("taskId"):
                first = (EMPTY_RULE_TASK, f"{path}.next.rules[{i}].taskId", "Next rule has no taskId.")
            if first:
                break
    if first:
        report.add(first[0], first[1], first[2], task_id)
    targets = [r.get("taskId") for r in rules] + ([next_["mergeTaskId"]] if next_.get("mergeTaskId") else [])
    for i, target in enumerate(targets):
        if target not in tasks:
            report.add(INVALID_NEXT_TASK, f"{path}.next", f"Next task {target!r} is not a task in this flow.", task_id)


def check_empty_dynamic(task_id, arguments, report):
    def walk(name, value, path):
        if not is_rows(value):
            return False
        found = False
        for i, row in enumerate(value):
            row_path = f"{path}[{i}].value"
            if walk(name, row.get("value"), row_path):
                found = True
                continue
            if row.get("type") == "context" and isinstance(row.get("value"), str) and not row["value"].strip():
                report.add(EMPTY_DYNAMIC_VALUE, row_path, f"Dynamic value is empty for argument {name}.", task_id)
                found = True
        return found

    for name in sorted(arguments):
        arg = arguments[name]
        if isinstance(arg, dict):
            walk(name, arg.get("value"), f"$.tasks.{task_id}.arguments.{name}.value")


def is_rows(value):
    return isinstance(value, list) and all(isinstance(r, dict) for r in value) and bool(value)


def check_action(tasks, task_id, task, path, arguments, actions, groups, report):
    action_id = task["action"]
    action = actions.get(action_id)
    if action is None:
        report.add(INVALID_ACTION, f"{path}.action",
                   f"Unknown or deprecated action {action_id!r}; pick one from references/catalog/actions/index.md.", task_id)
        return
    if action_id in NOT_RUNNABLE or (action.get("noExecutor") and not action.get("members")):
        instead = f"; use {NOT_RUNNABLE[action_id]}" if action_id in NOT_RUNNABLE else ""
        report.add(INVALID_ACTION, f"{path}.action",
                   f"Action {action_id} has no executor and fails the flow at runtime{instead}.", task_id)
        return
    if action.get("deprecated") and not action.get("members"):
        instead = f"; use {action['replacedBy']}" if action.get("replacedBy") else ""
        report.add("deprecated_action", f"{path}.action",
                   f"Action {action_id} is deprecated: it still runs, but new flows shouldn't use it{instead}.",
                   task_id, "warning")
    if action.get("members"):
        report.add(INVALID_ACTION, f"{path}.action",
                   f"Action {action_id} is an editor group, not a runnable action; use its members "
                   f"{action['members']} as tasks N and N.end.", task_id)
        return
    inputs = {i["name"]: i for i in action.get("inputs") or [] if isinstance(i, dict) and i.get("name")}
    group_inputs = {i.get("name") for g in groups.get(action_id, []) for i in g.get("inputs") or []}
    visible = [n for n, i in inputs.items() if i.get("visible")]

    for name in sorted(arguments):
        arg = arguments[name]
        arg_path = f"{path}.arguments.{name}"
        if name not in inputs:
            if name not in group_inputs:
                report.add(UNKNOWN_ARGUMENT, arg_path,
                           f"Action {action_id} has no input {name!r}, the engine ignores it; its inputs are: "
                           f"{', '.join(visible) or '(none visible)'}.", task_id)
            continue
        if not isinstance(arg, dict):
            report.add(INVALID_ARGUMENT_TYPE, arg_path,
                       f"Argument {name} must be an object {{\"type\": \"inline\", \"value\": ...}}; the engine crashes "
                       "on a null argument.", task_id)
            continue
        arg_type = arg.get("type", "")
        if arg_type == "context" and not isinstance(arg.get("value"), str):
            report.add(INVALID_ARGUMENT_TYPE, f"{arg_path}.value",
                       f"Argument {name} is context-typed, so its value must be a context key string.", task_id)
            continue
        # Context inputs receive the whole flow context whatever the argument says.
        if arg_type not in ("inline", "context") and inputs[name].get("type") != "context":
            report.add(INVALID_ARGUMENT_TYPE, f"{arg_path}.type",
                       f"Argument {name} has type {arg_type!r}; use \"inline\" (a value) or \"context\" (a context "
                       "key). Anything else reaches the action as nil.", task_id,
                       REQUIRED_INPUT_SEVERITY.get((action_id, name)) or "error")
            continue
        if (action_id, name) in ROW_LIST_INPUTS and arg_type == "inline" and not decodes_as_row_list(arg.get("value")):
            report.add(INVALID_ARGUMENT_TYPE, f"{arg_path}.value",
                       f"Argument {name} must be a list of {{key, type, value}} rows; any other value fails the step "
                       "when it runs.", task_id)
            continue
        check_row_types(task_id, name, arg.get("value"), f"{arg_path}.value", report)
        if name in ("provider", "defaultProvider") and action_id.startswith("oauth") and arg_type == "inline":
            provider = arg.get("value")
            if isinstance(provider, str) and provider and provider not in DEFAULT_OAUTH_PROVIDERS:
                report.add(OAUTH_PROVIDER_NOT_DEFAULT, f"{arg_path}.value",
                           f"OAuth provider {provider!r} is not set up in new projects; configure it in the "
                           "project's OAuth settings or the step fails with InvalidOAuthProvider.", task_id, "warning")
        if name in STEP_ID_INPUTS and arg_type == "inline":
            step = arg.get("value")
            if not (step in ("", None) and action_id == "connector") and (not isinstance(step, str) or step not in tasks):
                report.add(INVALID_STEP_REFERENCE, f"{arg_path}.value",
                           f"Argument {name} is {step!r}, which is not a task in this flow; it must name the task "
                           "the flow resumes at (\"N.end\" for task N).", task_id)

    for name, spec in inputs.items():
        # An absent boolean reads as false, which is a valid setting.
        if not spec.get("required") or not spec.get("visible") or spec.get("type") == "boolean" or name in arguments:
            continue
        severity = REQUIRED_INPUT_SEVERITY.get((action_id, name), "error")
        if severity:
            report.add(MISSING_REQUIRED_ARGUMENT, f"{path}.arguments",
                       f"Action {action_id} requires input {name!r}.", task_id, severity)

    if action_id != "connector":
        allowed = {"success"} | {s.get("id") for s in action.get("successes") or []} \
            | {e.get("type") for e in action.get("errors") or []}
        rules = (task.get("next") or {}).get("rules") if isinstance(task.get("next"), dict) else None
        for i, rule in enumerate(rules or []):
            interaction = rule.get("interactionId") if isinstance(rule, dict) else None
            if interaction and interaction not in allowed:
                report.add(INVALID_NEXT_TASK, f"{path}.next.rules[{i}].interactionId",
                           f"Action {action_id} does not declare interaction {interaction!r}, so this rule likely "
                           "never fires; use \"success\" or one of the action's error types.", task_id, "warning")

    # The editor gives both tasks of a two-step action the group's error handling, so a group's errors count too.
    # connector tasks also raise their template command's own error ids, which the catalog doesn't list.
    if action_id != "connector" and not action.get("templateCommandErrors"):
        declared = {e.get("type") for e in action.get("errors") or []} \
            | {e.get("type") for g in groups.get(action_id, []) for e in g.get("errors") or []}
        # The engine reads the legacy "errorHandling" map as errorHandlingV2 when the latter is empty.
        handling = task.get("errorHandlingV2") or task.get("errorHandling")
        for error_id in sorted(handling) if isinstance(handling, dict) else []:
            if error_id not in declared:
                report.add(INVALID_NEXT_TASK, f"{path}.errorHandlingV2.{error_id}",
                           f"Action {action_id} does not declare error {error_id!r}, so this handling likely never applies; "
                           "handle one of the action's error types.", task_id, "warning")


def check_success_route(task_id, task, path, actions, shared, report):
    """A succeeding step with no rule for "success" fails the flow (E102103) unless its action ends the flow
    (logged-in) or, in a subflow, "<id>.success" is a shared interaction the parent routes."""
    action = actions.get(task.get("action")) or {}
    if action.get("members") or task.get("action") not in actions:
        return
    rules = (task.get("next") or {}).get("rules") if isinstance(task.get("next"), dict) else None
    rules = [r for r in rules or [] if isinstance(r, dict)]
    if any(r.get("interactionId") == "success" for r in rules):
        return
    if (not rules and action.get("endTask")) or f"{task_id}.success" in shared:
        return
    report.add("E102103", f"{path}.next",
               f"Task has no next rule for \"success\" and {task.get('action')} does not end the flow; the flow fails "
               "here at runtime. Add a rule to the next step, or end with logged-in.", task_id, "warning")


def check_errors_before_screen(dsl, actions, report, subflow=False):
    """An action that runs before any screen has no screen to show an automatically handled error on, so the flow
    fails there. loadUser is left out: without a signed-in user, failing the flow is what step-up flows want."""
    tasks = dsl.get("tasks") if isinstance(dsl.get("tasks"), dict) else {}
    seen, stack = set(), [dsl.get("startTask"), "start"]
    while stack:
        task_id = stack.pop()
        task = tasks.get(task_id) if isinstance(task_id, str) else None
        if task_id in seen or not isinstance(task, dict) or task.get("type") in ("screen", "flow"):
            continue
        seen.add(task_id)
        rules = (task.get("next") or {}).get("rules") if isinstance(task.get("next"), dict) else None
        rules = [r for r in rules or [] if isinstance(r, dict)]
        stack.extend(r.get("taskId") for r in rules)
        action = actions.get(task.get("action")) or {}
        if task.get("type") != "automated" or task.get("action") == "loadUser":
            continue
        handling = task.get("errorHandlingV2") or task.get("errorHandling")
        routed = {r.get("interactionId") for r in rules} | {
            k for k, h in (handling.items() if isinstance(handling, dict) else ())
            if isinstance(h, dict) and h.get("errorHandlingType", "").startswith("custom")}
        unrouted = sorted({e.get("type") for e in action.get("errors") or []} - routed - {None})
        if unrouted and subflow:
            report.add("error_route_before_screen", f"$.tasks.{task_id}.errorHandlingV2",
                       f"Task runs before this subflow's first screen and leaves {', '.join(unrouted)} on automatic "
                       "handling. If the subflow runs before the parent flow shows any screen, these errors have no "
                       "screen to show on; route the ones you expect to a screen or another step (errorHandlingV2 "
                       "custom plus a next rule).", task_id, "info")
        elif unrouted:
            report.add("error_route_before_screen", f"$.tasks.{task_id}.errorHandlingV2",
                       f"Task runs before any screen and leaves {', '.join(unrouted)} on automatic handling, which has "
                       "no screen to show the error on, so the flow fails here. Route the errors you expect to a "
                       "screen or another step (errorHandlingV2 custom plus a next rule).", task_id, "info")


def check_known_outcomes(dsl, report):
    """Outcomes the password recipes (passwords-sign-up-or-in-verify-email, passwords-reset-by-link) handle and
    composed flows tend to drop: an expired password, a forgotten one, and an email never
    verified after a password sign-up. Locked and disabled users are left out: every recipe and content template
    leaves UserTemporarilyLocked and UserDisabled to automatic handling, which shows the error on the screen."""
    tasks = dsl.get("tasks") if isinstance(dsl.get("tasks"), dict) else {}
    tasks = {k: t for k, t in tasks.items() if isinstance(t, dict)}
    actions = {str(t.get("action") or "") for t in tasks.values()}
    sign_ins = sorted(k for k, t in tasks.items() if str(t.get("action") or "").startswith("password-sign-in"))
    for task_id in sign_ins:
        rules = (tasks[task_id].get("next") or {}).get("rules") if isinstance(tasks[task_id].get("next"), dict) else []
        if not any(isinstance(r, dict) and r.get("interactionId") == "PasswordExpired" for r in rules or []):
            report.add("outcome_not_routed", f"$.tasks.{task_id}.next",
                       "Password sign-in has no PasswordExpired route, so a user whose password expired gets an error "
                       "and can't sign in. The password recipes route it to a replace-password screen "
                       "(errorHandlingV2 PasswordExpired custom plus a next rule); keep that, or name the removal in "
                       "the report.", task_id, "warning")
    if not sign_ins:
        return
    if not any(a.startswith("password-send-reset") or a == "password-update" for a in actions):
        report.add("outcome_not_routed", f"$.tasks.{sign_ins[0]}",
                   "The flow signs in with a password but has no forgot-password path (no password-send-reset* or "
                   "password-update step). The password recipes offer one from the sign-in screen; keep it, or name "
                   "the removal in the report.", sign_ins[0], "warning")
    if "password-sign-up" in actions and "verifiedEmail" not in json.dumps(
            [t.get("conditions") for t in tasks.values() if t.get("type") == "condition"]):
        report.add("outcome_not_routed", f"$.tasks.{sign_ins[0]}.next",
                   "The flow signs users up with a password but never checks user.verifiedEmail after sign-in, so a "
                   "user who left before verifying the email signs in unverified. passwords-sign-up-or-in-verify-email "
                   "checks it after sign-in and sends a code; keep that, or name the removal in the report.",
                   sign_ins[0], "warning")


def flow_ids(flow):
    """Screen ids and condition ids: random per flow, so a flow made by copying a recipe keeps some of its."""
    contents = flow.get("contents") if isinstance(flow.get("contents"), dict) else {}
    tasks = contents.get("tasks") if isinstance(contents.get("tasks"), dict) else {}
    ids = {s.get("screenId") for s in flow.get("screens") or [] if isinstance(s, dict)}
    for task in tasks.values():
        if not isinstance(task, dict):
            continue
        ids.add(task.get("screenId"))
        ids |= {c.get("interactionId") for c in task.get("conditions") or [] if isinstance(c, dict)}
    return {i for i in ids if isinstance(i, str) and i and i != "ELSE"}


def check_recipe_origin(flow, report):
    ids = flow_ids(flow)
    if not ids or not RECIPES.is_dir():
        return
    for path in RECIPES.glob("*/flow.json"):
        try:
            if ids & flow_ids(json.loads(path.read_text())):
                return
        except (OSError, ValueError, AttributeError):
            continue
    report.add("flow_not_from_recipe", "$",
               "This flow matches no recipe: none of its screen or condition ids is a recipe's. Fine for a console "
               "export or template; a new flow should start from the nearest recipe's flow.json (SKILL.md step 1), "
               "since recipes carry the tested wiring a hand-written flow tends to miss.", severity="info")


def decodes_as_row_list(value):
    """The engine parses an object input's string as JSON (unparsable or "" -> nothing), then decodes the value into
    a row list: a boolean, number or object fails."""
    if value is None or isinstance(value, list):
        return True
    if isinstance(value, str):
        try:
            return not isinstance(json.loads(value), dict)
        except ValueError:
            return True
    return False


def check_row_types(task_id, name, value, path, report):
    if not is_rows(value) or not all("key" in r or "type" in r for r in value):
        return
    for i, row in enumerate(value):
        row_path = f"{path}[{i}]"
        check_row_types(task_id, name, row.get("value"), f"{row_path}.value", report)
        if row.get("key") and row.get("type") not in ROW_TYPES:
            report.add(INVALID_ARGUMENT_TYPE, f"{row_path}.type",
                       f"Argument {name} row {row.get('key')!r} has type {row.get('type')!r}, which the flow editor "
                       "cannot show; use string, number, boolean, object, array or context.", task_id, "warning")


def optional_pass(module_name, function, flow):
    """Runs a sibling module's check when the module is there; its bugs never hide the main results."""
    if not (HERE / f"{module_name}.py").exists():
        return []
    sys.path.insert(0, str(HERE))
    try:
        module = __import__(module_name)
        return getattr(module, function)(flow)
    except Exception as err:
        return [{"code": f"{module_name}_crash", "path": "", "message": f"{module_name}.py failed: {err!r}"}]


def validate(data):
    report = Report()
    if not isinstance(data, dict):
        report.add("shape_not_object", "$", "The file must be a JSON object.")
        return report, []
    actions, conditions = load_catalog()
    flow, dsl = unwrap(data, report)
    shared = dsl.get("sharedInteractions") if isinstance(dsl, dict) else None
    if shared is None and flow is not None and isinstance(flow.get("metadata"), dict):
        shared = flow["metadata"].get("sharedInteractions")
    shared = {i.get("id") for i in shared or [] if isinstance(i, dict)}
    check_dsl(dsl, actions, conditions, report, shared)
    if isinstance(dsl, dict) and isinstance(dsl.get("tasks"), dict):
        check_condition_keys(dsl["tasks"], conditions, load_context_keys(), report)
        check_errors_before_screen(dsl, actions, report, subflow=bool(shared))
        check_known_outcomes(dsl, report)
    if flow is not None:
        check_recipe_origin(flow, report)
    style = []
    if flow is not None:
        for item in optional_pass("flow_screens", "check_screens", flow):
            severity = item.pop("severity", "error")
            {"warning": report.warnings, "info": report.info}.get(severity, report.errors).append(item)
        style = optional_pass("flow_style", "check_style", flow)
    return report, style


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a Descope flow JSON file before importing it.")
    parser.add_argument("flow", help="flow JSON file")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.flow).read_text())
    except (OSError, ValueError) as err:
        print(f"cannot read {args.flow}: {err}", file=sys.stderr)
        return 2
    report, style = validate(data)
    ok = not report.errors
    if args.json:
        print(json.dumps({"ok": ok, "errors": report.errors, "warnings": report.warnings, "info": report.info,
                          "style": style}, indent=2))
    else:
        for kind, items in (("error", report.errors), ("warning", report.warnings), ("info", report.info),
                            ("style", style)):
            for item in items:
                where = f"task {item['taskId']} " if item.get("taskId") else ""
                where += f"screen {item['screenId']} " if item.get("screenId") else ""
                print(f"{kind} {item['code']} {where}{item['path'] or '-'}: {item['message']}")
        print(f"{len(report.errors)} errors, {len(report.warnings)} warnings, {len(report.info)} info, "
              f"{len(style)} style notes"
              + ("" if ok else ": fix every error and run again"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
