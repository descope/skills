#!/usr/bin/env python3
"""Compare a flow with the recipes it was built from. Python 3 standard library only.

    python3 recipe_diff.py <flow.json> --recipe recipes/<base>/flow.json [--recipe recipes/<other>/flow.json@<offset> ...]

The first --recipe is the base: its task ids are kept. Each added recipe's numeric task ids are shifted by its
offset (task 5 at @100 is task 105, 5.end is 105.end); its other ids ("start") keep their name. Screens keep their
screenId; a screen whose id isn't a recipe's is matched by its screen task's name.

Prints plain text, removals first: what the recipes have and the flow doesn't (tasks, routes, screens, screen
components), then what changed, then what the flow adds ("generated, not from a recipe"). Quote it in the report.
Exit 0, or 1 when a file can't be read.
"""

import argparse
import json
import re
import sys
from pathlib import Path

NUMERIC_ID = re.compile(r"^(\d+)(.*)$")
STEP_ID_INPUTS = ("exchangeStepId", "verifyStepId", "finishStepId")
# Node props that only lay out or style a component: a change there is not worth a line.
LAYOUT_PROPS = {"id", "data-editor-type", "st-items-grow", "background", "paddingX", "paddingY", "spaceBetween",
                "width", "align", "justify", "direction", "full-width", "text-align", "color", "shape", "size",
                "variant", "italic"}


def load(path):
    data = json.loads(Path(path).read_text())
    flow = data["flow"] if isinstance(data, dict) and isinstance(data.get("flow"), dict) else data
    if not isinstance(flow, dict):
        raise ValueError("not a flow object")
    contents = flow.get("contents") or flow.get("dsl") or flow
    if not isinstance(contents, dict):
        raise ValueError("contents is not an object")
    tasks = contents.get("tasks") if isinstance(contents.get("tasks"), dict) else {}
    screens = flow.get("screens") or data.get("screens") or []
    if isinstance(screens, dict):
        screens = [dict(v, screenId=v.get("screenId", k)) for k, v in screens.items() if isinstance(v, dict)]
    screens = {s.get("screenId"): s for s in screens if isinstance(s, dict) and s.get("screenId")}
    return {k: v for k, v in tasks.items() if isinstance(v, dict)}, screens


def shift(task_id, offset):
    if not offset or not isinstance(task_id, str):
        return task_id
    m = NUMERIC_ID.match(task_id)
    return f"{int(m.group(1)) + offset}{m.group(2)}" if m else task_id


def as_dict(x):
    return x if isinstance(x, dict) else {}


def as_list(x):
    return x if isinstance(x, list) else []


def rules(task):
    return [r for r in as_list(as_dict(task.get("next")).get("rules")) if isinstance(r, dict)]


def shifted_task(task, offset):
    """A copy of the task with every task id it names shifted."""
    task = json.loads(json.dumps(task))
    if not offset:
        return task
    task["id"] = shift(task.get("id"), offset)
    for rule in rules(task):
        if "taskId" in rule:
            rule["taskId"] = shift(rule["taskId"], offset)
    for name in STEP_ID_INPUTS:
        arg = as_dict(task.get("arguments")).get(name)
        if isinstance(arg, dict) and isinstance(arg.get("value"), str):
            arg["value"] = shift(arg["value"], offset)
    return task


def routes(task):
    """(interactionId, target task id) of each next rule ("" for a rule with no interaction); an interaction may
    have several rules (magic link: success -> wait screen and success -> N.end)."""
    return [(r.get("interactionId") or "", r.get("taskId")) for r in rules(task)]


def route(task_id, iid, target):
    return f"route {task_id} --{iid or '(next)'}--> {target}"


def route_changes(task_id, have, want, src):
    """Removed, changed and added routes, per interaction: a single target swapped for another is a change."""
    removed, changed, added = [], [], []
    title = f'("{have.get("name") or ""}")'
    have, want = routes(have), routes(want)
    for iid in dict.fromkeys(i for i, _ in want + have):
        w = [t for i, t in want if i == iid]
        h = [t for i, t in have if i == iid]
        gone = [t for t in w if t not in h or w.count(t) > h.count(t)]
        new = [t for t in h if t not in w or h.count(t) > w.count(t)]
        if len(gone) == 1 and len(new) == 1:
            changed.append(f"{route(task_id, iid, gone[0])} now goes to {new[0]} [{src}]")
            continue
        removed += [f"{route(task_id, iid, t)} {title} [{src}]" for t in dict.fromkeys(gone)]
        added += [f"{route(task_id, iid, t)} (generated, not from a recipe)" for t in dict.fromkeys(new)]
    return removed, changed, added


def label(task_id, task):
    kind = task.get("action") or task.get("type") or "task"
    return f'task {task_id} "{task.get("name") or ""}" ({kind})'


def origin(src):
    name, offset, old_id = src
    return f"{name}, was {old_id}" if offset and old_id is not None else name


def task_changes(task, want):
    """What differs between the flow's task and the recipe's, one phrase each (routes are compared elsewhere)."""
    changes = []
    for field in ("screenId", "name"):
        if task.get(field) != want.get(field):
            changes.append(f"{field} {want.get(field)!r} -> {task.get(field)!r}")
    have_args, want_args = as_dict(task.get("arguments")), as_dict(want.get("arguments"))
    for key in sorted(set(want_args) - set(have_args)):
        changes.append(f"argument {key} removed")
    for key in sorted(set(have_args) - set(want_args)):
        changes.append(f"argument {key} added")
    for key in sorted(set(have_args) & set(want_args)):
        if have_args[key] != want_args[key]:
            changes.append(f"argument {key} changed")
    have_err, want_err = as_dict(task.get("errorHandlingV2")), as_dict(want.get("errorHandlingV2"))
    for key in sorted(set(want_err) | set(have_err)):
        a = (want_err.get(key) or {}).get("errorHandlingType") if isinstance(want_err.get(key), dict) else None
        b = (have_err.get(key) or {}).get("errorHandlingType") if isinstance(have_err.get(key), dict) else None
        if a != b:
            changes.append(f"error {key} handling {a or 'none'} -> {b or 'none'}")
    have_cond = {c.get("interactionId"): c for c in as_list(task.get("conditions")) if isinstance(c, dict)}
    want_cond = {c.get("interactionId"): c for c in as_list(want.get("conditions")) if isinstance(c, dict)}
    for key in want_cond:
        if key not in have_cond:
            changes.append(f"condition branch {key} removed")
        elif have_cond[key] != want_cond[key]:
            changes.append(f"condition branch {key} changed")
    changes += [f"condition branch {key} added" for key in have_cond if key not in want_cond]
    return changes


def components(screen):
    """{node id: (component, what it shows)} for the screen's components other than layout containers."""
    out = {}
    contents = screen.get("contents") if isinstance(screen.get("contents"), dict) else {}
    for node_id, node in contents.items():
        if not isinstance(node, dict) or node_id == "ROOT":
            continue
        t = node.get("type")
        name = t.get("resolvedName") if isinstance(t, dict) else t
        if name in ("Container", "Canvas"):
            continue
        props = node.get("props") if isinstance(node.get("props"), dict) else {}
        shown = props.get("name") or props.get("children") or props.get("text") or props.get("label") or ""
        out[node_id] = (name, str(shown)[:60], props)
    return out


def describe(node_id, comp):
    name, shown, _ = comp
    return f'{name} "{shown}" ({node_id})' if shown else f"{name} ({node_id})"


def screen_changes(have, want):
    removed, changed, added = [], [], []
    a, b = components(want), components(have)
    for node_id in a:
        if node_id not in b:
            removed.append(f"component {describe(node_id, a[node_id])}")
        else:
            pa, pb = a[node_id][2], b[node_id][2]
            keys = sorted(k for k in set(pa) | set(pb) if k not in LAYOUT_PROPS and pa.get(k) != pb.get(k))
            if a[node_id][0] != b[node_id][0]:
                changed.append(f"component {node_id}: {a[node_id][0]} -> {b[node_id][0]}")
            elif keys:
                changed.append(f"component {describe(node_id, b[node_id])}: props {', '.join(keys)}")
    added = [f"component {describe(node_id, b[node_id])}" for node_id in b if node_id not in a]
    return removed, changed, added


def parse_recipe(arg, first):
    m = re.fullmatch(r"(.+)@(\d+)", arg)
    if m:
        return m.group(1), int(m.group(2))
    if not first:
        raise ValueError(f"--recipe {arg}: an added recipe needs @<offset> (the shift of its task ids)")
    return arg, 0


def screen_task(sid, tasks):
    """(task id, task) of the first task that shows the screen."""
    return next(((k, t) for k, t in tasks.items() if t.get("screenId") == sid), (None, {}))


def diff(flow_path, recipe_args):
    tasks, screens = load(flow_path)
    expected, sources, notes = {}, {}, []
    recipe_screens = {}  # (recipe name, screenId) -> (screen, name of the task showing it, shifted task id)
    for n, arg in enumerate(recipe_args):
        path, offset = parse_recipe(arg, n == 0)
        name = Path(path).parent.name or Path(path).stem
        r_tasks, r_screens = load(path)
        for old_id, task in r_tasks.items():
            new_id = shift(old_id, offset)
            if new_id in expected:
                if NUMERIC_ID.match(old_id):  # every recipe has a "start"; the base's is kept
                    notes.append(f"{name} task {old_id} -> {new_id} collides with {origin(sources[new_id])}; "
                                 "the first recipe's is compared")
                continue
            expected[new_id] = shifted_task(task, offset)
            sources[new_id] = (name, offset, old_id)
        for sid, screen in r_screens.items():
            shared = [r for r, s in recipe_screens if s == sid]
            if shared:
                notes.append(f"{name} screen {sid} is also in {shared[0]}; a flow with both needs a new id on one")
            task_id, task = screen_task(sid, r_tasks)
            recipe_screens[(name, sid)] = (screen, task.get("name"), shift(task_id, offset))

    removed, changed, added = [], [], []
    for task_id, want in expected.items():
        src = origin(sources[task_id])
        if task_id not in tasks:
            removed.append(f"{label(task_id, want)} [{src}]")
            continue
        have = tasks[task_id]
        if (have.get("type"), have.get("action")) != (want.get("type"), want.get("action")):
            # The id was reused for another step: the recipe's step is gone, the flow's is new.
            removed.append(f"{label(task_id, want)} [{src}], its id now used by \"{have.get('name') or ''}\"")
            added.append(f"{label(task_id, have)} (generated, not from a recipe)")
            added += [f"{route(task_id, i, t)} (generated, not from a recipe)" for i, t in routes(have)]
            continue
        for phrase in task_changes(have, want):
            changed.append(f"{label(task_id, have)}: {phrase} [{src}]")
        r, c, a = route_changes(task_id, have, want, src)
        removed += r
        changed += c
        added += a
    for task_id, task in tasks.items():
        if task_id not in expected:
            added.append(f"{label(task_id, task)} (generated, not from a recipe)")
            added += [f"{route(task_id, i, t)} (generated, not from a recipe)" for i, t in routes(task)]

    # Screens: by id first, then by the (shifted) id of the task showing them, then by that task's name.
    match, taken = {}, set()
    passes = (lambda sid, tid, name, key, info: key[1] == sid,
              lambda sid, tid, name, key, info: tid is not None and info[2] == tid,
              lambda sid, tid, name, key, info: bool(name) and info[1] == name)
    for test in passes:
        for sid in screens:
            if sid in match:
                continue
            tid, task = screen_task(sid, tasks)
            key = next((k for k, info in recipe_screens.items()
                        if k not in taken and test(sid, tid, task.get("name"), k, info)), None)
            if key:
                match[sid] = key
                taken.add(key)
    for sid, screen in screens.items():
        name = screen_task(sid, tasks)[1].get("name") or ""
        title = f'screen {sid} "{name}"'
        if sid not in match:
            added.append(f"{title} (generated, not from a recipe)")
            continue
        src, want_id = match[sid]
        if want_id != sid:
            changed.append(f"{title}: copy of {want_id} under a new id [{src}]")
        r, c, a = screen_changes(screen, recipe_screens[match[sid]][0])
        removed += [f"{title}: {x} [{src}]" for x in r]
        changed += [f"{title}: {x} [{src}]" for x in c]
        added += [f"{title}: {x} (generated, not from a recipe)" for x in a]
    # A task now showing a copy of its recipe screen: the copy line above says it.
    copies = {(f"screenId {want_id!r} -> {sid!r}") for sid, (_, want_id) in match.items() if want_id != sid}
    changed = [c for c in changed if not any(f": {x} [" in c for x in copies)]
    for key, info in recipe_screens.items():
        if key not in taken:
            removed.append(f'screen {key[1]} "{info[1] or ""}" [{key[0]}]')
    return removed, changed, added, notes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("flow")
    parser.add_argument("--recipe", action="append", required=True,
                        help="recipe flow.json; the first is the base, others take @<offset>")
    args = parser.parse_args(argv)
    try:
        removed, changed, added, notes = diff(args.flow, args.recipe)
    except (OSError, ValueError, AttributeError, TypeError) as err:
        print(f"recipe_diff: can't read input: {err}", file=sys.stderr)
        return 1
    recipes = ", ".join(args.recipe)
    print(f"recipe_diff {args.flow} against {recipes}")
    print(f"{len(removed)} removed, {len(changed)} changed, {len(added)} added")
    for title, lines in (("REMOVED (in a recipe, not in the flow)", removed), ("CHANGED", changed),
                         ("ADDED", added), ("NOTES", notes)):
        if lines or title != "NOTES":
            print(f"\n{title}:")
            print("\n".join(f"- {line}" for line in lines) if lines else "- none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
