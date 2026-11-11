"""Console-likeness checks for a flow JSON file: does it look like what the console editor saves?

These never make a flow invalid; validate_flow.py reports them under "style". Every finding has a stable code
(style_*), a path into the file and a message; style_view_grid comes once per flow, with "paths" listing every
place. There is no check for absent optional inputs: console-made flows usually leave them out.

    check_style(flow: dict) -> list[{"code", "path", "message"}]

`flow` is an ExportedFlow ({flowId, metadata, contents, screens}).
"""

import json
import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "references" / "catalog" / "actions.json"

TASK_ID_RE = re.compile(r"^\d+(\.end)?$")
SCREEN_ID_RE = re.compile(r"^SC[0-9A-Za-z]{27}$")
NODE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10}$")
NODE_ID_EXCEPTIONS = {"ROOT", "resend", "oneTimeCodeId"}
CONDITION_ID_RE = re.compile(r"^[0-9a-z]{10,11}$")
GRID = 12
# Older editor names still on most console-made flows (prod, 2026-10-22): logged-in was "Generate JWT", and
# update-user-properties was "Update User / Properties" (10,222 prod tasks vs 2,929 "Attributes").
EXTRA_NAMES = {"logged-in": {"Generate JWT"}, "update-user-properties": {"Update User / Properties"}}
# Steps the console's users name for what they do (only 11% of prod scriptlets keep "Scriptlet").
CUSTOM_NAMED = {"connector", "scriptlet", "generate-audit-event"}


def load_catalog():
    try:
        return json.loads(CATALOG.read_text()).get("actions") or {}
    except (OSError, ValueError):
        return {}


def check_style(flow):
    findings = []

    def add(code, path, message):
        findings.append({"code": code, "path": path, "message": message})

    contents = flow.get("contents") if isinstance(flow.get("contents"), dict) else {}
    tasks = contents.get("tasks") if isinstance(contents.get("tasks"), dict) else {}
    tasks = {k: t for k, t in tasks.items() if isinstance(t, dict)}
    actions = load_catalog()
    groups = {}
    for group in actions.values():
        for member in group.get("members") or []:
            groups.setdefault(member, []).append(group)

    check_ids_and_start(contents, tasks, add)
    for task_id, task in sorted(tasks.items()):
        path = f"$.contents.tasks.{task_id}"
        check_view(task, path, add)
        if task.get("type") == "automated" and actions:
            check_automated(task, path, actions, groups, add)
        if task.get("type") == "condition":
            check_conditions(task, path, add)
        if task_id.endswith(".end") and task_id[:-4] in tasks:
            parent = tasks[task_id[:-4]]
            if task.get("name") != parent.get("name") or task.get("view") != parent.get("view"):
                add("style_end_mismatch", path, f"{task_id} should have the same name and view as {task_id[:-4]}.")
    check_edges(tasks, contents.get("startTask"), add)
    findings = aggregate(findings, ("style_view_grid",))
    for i, screen in enumerate(flow.get("screens") or []):
        if isinstance(screen, dict):
            check_screen(screen, f"$.screens[{i}]", add)
    return findings


def aggregate(findings, codes):
    """Folds systemic findings into one per code, so one off-grid layout doesn't count as forty findings."""
    out, folded = [], {}
    for item in findings:
        if item["code"] not in codes:
            out.append(item)
            continue
        if item["code"] in folded:
            folded[item["code"]]["paths"].append(item["path"])
            continue
        folded[item["code"]] = {"code": item["code"], "path": item["path"], "message": item["message"],
                                "paths": [item["path"]]}
        out.append(folded[item["code"]])
    for item in folded.values():
        if len(item["paths"]) > 1:
            item["message"] = f"{len(item['paths'])} places, first: {item['message']}"
        else:
            del item["paths"]
    return out


def check_ids_and_start(contents, tasks, add):
    for task_id, task in sorted(tasks.items()):
        if task_id != "start" and not TASK_ID_RE.match(task_id):
            add("style_task_id", f"$.contents.tasks.{task_id}",
                f"Task id {task_id!r}: the console numbers tasks 0, 1, 2, ... and uses N.end for two-step actions.")
        if task.get("id") not in (None, task_id):
            add("style_task_id_key", f"$.contents.tasks.{task_id}.id", "Task id differs from its key.")
    if "start" not in tasks:
        add("style_start_missing", "$.contents.tasks",
            'No "start" node: console flows have {"id": "start", "name": "start", "next": {"rules": [{"taskId": ...}]}}.')
    if contents.get("startTask") == "start":
        add("style_start_task", "$.contents.startTask", 'startTask should be the first real task, not "start".')


def check_view(task, path, add):
    view = task.get("view")
    if not isinstance(view, dict):
        add("style_view_missing", f"{path}.view", "Task has no view position.")
        return
    for axis in ("x", "y"):
        value = view.get(axis)
        if not isinstance(value, (int, float)) or value % GRID:
            add("style_view_grid", f"{path}.view.{axis}", f"view.{axis}={value!r} is not on the console's 12px grid.")


def check_automated(task, path, actions, groups, add):
    action_id = task.get("action")
    action = actions.get(action_id)
    if not action:
        return
    member_of = groups.get(action_id) or []
    names = {action.get("displayName")} | {g.get("displayName") for g in member_of} | EXTRA_NAMES.get(action_id, set())
    names.discard(None)
    if action_id not in CUSTOM_NAMED and names and task.get("name") not in names:
        add("style_task_name", f"{path}.name",
            f"Name {task.get('name')!r}: the console names this step {' or '.join(map(repr, sorted(names)))}.")


def check_conditions(task, path, add):
    conditions = task.get("conditions") if isinstance(task.get("conditions"), list) else []
    for i, condition in enumerate(conditions):
        interaction = condition.get("interactionId") if isinstance(condition, dict) else None
        if interaction == "ELSE":
            if i != len(conditions) - 1:
                add("style_else_last", f"{path}.conditions[{i}]", "ELSE should be the last condition.")
        elif not isinstance(interaction, str) or not CONDITION_ID_RE.match(interaction):
            add("style_condition_id", f"{path}.conditions[{i}].interactionId",
                f"Condition id {interaction!r}: the console uses 10-11 random chars of [0-9a-z].")


def successors(task):
    rules = (task.get("next") or {}).get("rules") if isinstance(task.get("next"), dict) else None
    return [r.get("taskId") for r in rules or [] if isinstance(r, dict)]


def reaches(tasks, start, goal):
    seen, stack = set(), [start]
    while stack:
        task_id = stack.pop()
        if task_id == goal:
            return True
        if task_id in seen or task_id not in tasks:
            continue
        seen.add(task_id)
        stack.extend(successors(tasks[task_id]))
    return False


def depths(tasks, start):
    """Steps from the start task (and the start node) to each task it reaches."""
    depth, queue = {}, [(t, 0) for t in (start, "start") if t in tasks]
    while queue:
        task_id, d = queue.pop(0)
        if task_id in depth or task_id not in tasks:
            continue
        depth[task_id] = d
        queue.extend((t, d + 1) for t in successors(tasks[task_id]))
    return depth


def check_edges(tasks, start, add):
    """Edges should run left to right; a back link (resend, retry, back: an edge to an earlier task, 11% of prod
    edges) or an edge that closes a loop may point left."""
    depth = depths(tasks, start)
    for task_id, task in sorted(tasks.items()):
        rules = (task.get("next") or {}).get("rules") if isinstance(task.get("next"), dict) else None
        x = (task.get("view") or {}).get("x") if isinstance(task.get("view"), dict) else None
        for i, rule in enumerate(rules or []):
            target = tasks.get(rule.get("taskId")) if isinstance(rule, dict) else None
            target_x = (target.get("view") or {}).get("x") if target and isinstance(target.get("view"), dict) else None
            if (isinstance(x, (int, float)) and isinstance(target_x, (int, float)) and target_x < x
                    and depth.get(rule.get("taskId"), -1) >= depth.get(task_id, -1)
                    and not reaches(tasks, rule.get("taskId"), task_id)):
                add("style_edge_backward", f"$.contents.tasks.{task_id}.next.rules[{i}]",
                    f"Edge to {rule.get('taskId')} goes right to left; console flows run left to right.")


def check_screen(screen, path, add):
    screen_id = screen.get("screenId")
    if isinstance(screen_id, str) and not SCREEN_ID_RE.match(screen_id):
        add("style_screen_id", f"{path}.screenId",
            f"Screen id {screen_id!r}: the console's are 'SC' + 27 base62 chars.")
    nodes = screen.get("contents") if isinstance(screen.get("contents"), dict) else {}
    for node_id, node in sorted(nodes.items()):
        if not isinstance(node, dict):
            continue
        node_path = f"{path}.contents.{node_id}"
        if node_id not in NODE_ID_EXCEPTIONS and not NODE_ID_RE.match(node_id):
            add("style_node_id", node_path, f"Node id {node_id!r}: the editor uses 10-char nanoids.")
        props = node.get("props") if isinstance(node.get("props"), dict) else {}
        if node_id != "ROOT" and props.get("id") not in (None, node_id):
            add("style_node_props_id", f"{node_path}.props.id", "props.id differs from the node id.")
        if "displayName" not in node or "custom" not in node:
            add("style_node_shape", node_path, "The editor writes displayName and custom on every node.")
