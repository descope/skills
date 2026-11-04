#!/usr/bin/env python3
"""Screen-content checks for a flow JSON (the ExportedFlow shape), used by validate_flow.py beside it.

check_screens(flow) returns a list of {"code", "path", "message", "severity", "taskId"?, "screenId"?}.
The component list comes from ../references/catalog/screens/components.json. Interactions and input keys are derived
the way the console derives them. Malformed shapes are reported, never raised.

Standalone: python3 flow_screens.py <flow.json>... [--json]
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_JSON = os.path.join(HERE, "..", "references", "catalog", "screens", "components.json")

# The MCP flow import rejects any other key on a screen.
SCREEN_KEYS = {"screenId", "interactions", "contents"}

# The console adds "polling-error" with every polling node. A screen that leaves it out of screen.interactions gets
# the old behavior (an expired link returns an error to the client); one that lists it turns the expiry into that
# interaction, which then needs a next rule.
OPTIONAL_INTERACTIONS = {"polling-error"}

# Editor and theme attributes any component may carry besides its knownProps.
FREE_PROP_PREFIXES = ("data-", "aria-", "st-")

# CraftJS's built-in canvas type; the editor's restoreType accepts it besides the resolver's names.
BUILTIN_COMPONENTS = {"Canvas"}

_components = None


# Components whose text the web component fills from {{key}}, and the screen state the server sends whatever
# contextKeys lists (inputs is form's old name). Every other key is sent only when the screen task lists it.
TEMPLATED_COMPONENTS = {"Text", "Link", "CodeSnippet"}
TEMPLATE_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
UNLISTED_PREFIXES = ("sentTo.", "form.", "inputs.", "totp.", "notp.", "sso.", "project.")
UNLISTED_KEYS = {"linkId", "errorText", "errorType", "selfProvisionDomains", "tenantEmailDomains"}


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, (dict, list)):
        for v in (x.values() if isinstance(x, dict) else x):
            yield from strings(v)


def components():
    global _components
    if _components is None:
        with open(COMPONENTS_JSON) as f:
            _components = json.load(f)
    return _components


def as_dict(x):
    return x if isinstance(x, dict) else {}


def as_list(x):
    return x if isinstance(x, list) else []


def as_str(x):
    """A usable id: a non-empty string, else None."""
    return x if isinstance(x, str) and x else None


def resolved_name(node):
    t = node.get("type")
    name = t.get("resolvedName") if isinstance(t, dict) else t
    return name if isinstance(name, str) else None


def version_at_least(version, minimum):
    try:
        have = tuple(int(p) for p in str(version).split("-")[0].split("."))
    except ValueError:
        return False
    return have >= minimum


def resolve_input_key(name, components_version):
    """The input key the console saves for an input name."""
    if name == "newPassword" and version_at_least(components_version, (3, 0, 9)):
        return "newPassword_noPolicyOverrides"
    return name


def canonical_key(key):
    """The console spells newPassword per the project's components version, which a flow file doesn't know."""
    return "newPassword" if key == "newPassword_noPolicyOverrides" else key


def node_interactions(node):
    """The interaction ids a node adds to its screen, as the console computes them."""
    ctype = as_dict(node.get("custom")).get("type")
    props = as_dict(node.get("props"))
    if ctype == "button":
        return [as_str(props.get("id"))]
    if ctype == "input" and props.get("autoComplete") == "webauthn":
        return [as_str(props.get("id"))]
    if ctype == "polling":
        return ["polling", "polling-error"]
    if ctype == "oneTimeCode" and props.get("data-auto-submit"):
        return [as_str(props.get("id"))]
    return []


def check_screens(flow):
    out = []

    def add(severity, code, path, message, **extra):
        item = {"code": code, "path": path, "message": message, "severity": severity}
        item.update({k: v for k, v in extra.items() if v is not None})
        out.append(item)

    if not isinstance(flow, dict):
        add("error", "flow_bad_shape", "$", "flow is not an object")
        return out

    catalog = components()
    known = catalog["components"]
    aliases = catalog["aliases"]
    metadata = as_dict(flow.get("metadata"))
    contents_dsl = as_dict(flow.get("contents"))
    tasks = as_dict(contents_dsl.get("tasks"))
    screens = flow.get("screens")
    if screens is not None and not isinstance(screens, list):
        add("error", "screen_bad_shape", "$.screens", "screens must be a list")
    screens = as_list(screens)
    # A subflow's exits: metadata.sharedInteractions (where the console writes them) or contents'.
    shared = {as_str(i.get("id")) for i in as_list(contents_dsl.get("sharedInteractions"))
              + as_list(metadata.get("sharedInteractions")) if isinstance(i, dict)}
    version = metadata.get("componentsVersion")
    if screens and not version:
        add("error", "components_version_missing", "$.metadata.componentsVersion",
            "flows with screens need metadata.componentsVersion (e.g. \"2.1.13\"); without it import migrates the "
            "screens as version 1.0.0 and renames props")

    derived = {}  # screenId -> set of interaction ids its nodes produce
    listed_by_screen = {}  # screenId -> set of ids in screen.interactions
    input_keys = {}  # screenId -> (inputKeys, allInputKeys)
    templated = {}  # screenId -> {context key used as {{key}}: first node path}
    unreadable = set()  # screen ids whose contents could not be read: their tasks are not checked further
    seen_ids = {}
    for i, screen in enumerate(screens):
        sp = f"$.screens[{i}]"
        if not isinstance(screen, dict):
            add("error", "screen_bad_shape", sp, "screen is not an object")
            continue
        sid = as_str(screen.get("screenId"))
        if not sid:
            add("error", "screen_id_missing", sp, "screen has no screenId (a non-empty string)")
            continue
        if sid in seen_ids:
            add("error", "screen_duplicate_id", sp, f"screenId {sid!r} also used by $.screens[{seen_ids[sid]}]",
                screenId=sid)
        seen_ids[sid] = i
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
            add("error", "screen_id_invalid", f"{sp}.screenId",
                f"screenId {sid!r} must match [A-Za-z0-9_-]+ (import rejects it)", screenId=sid)
        if sid.startswith("new-") and as_dict(tasks.get(sid[4:])).get("screenId") != sid:
            add("error", "screen_id_reserved", f"{sp}.screenId",
                f"screenId {sid!r} starts with 'new-', which import treats as the editor placeholder for task "
                f"{sid[4:]!r}'s new screen; pick another id", screenId=sid)
        extra = sorted(str(k) for k in set(screen) - SCREEN_KEYS)
        if extra:
            add("error", "screen_extra_key", sp,
                f"screen keys must be only screenId, interactions, contents; found {', '.join(extra)}", screenId=sid)
        contents = screen.get("contents")
        if not isinstance(contents, dict) or not contents:
            add("error", "screen_empty", f"{sp}.contents", "screen has no contents (CraftJS node map)", screenId=sid)
            unreadable.add(sid)
            continue
        cp = f"{sp}.contents"

        root = contents.get("ROOT")
        if not isinstance(root, dict):
            add("error", "screen_bad_root", cp, "contents has no ROOT node", screenId=sid)
        else:
            if resolved_name(root) != "Container":
                add("error", "screen_bad_root", f"{cp}.ROOT",
                    f"ROOT must be a Container, found {resolved_name(root)!r}", screenId=sid)
            if root.get("parent"):
                add("error", "screen_bad_root", f"{cp}.ROOT.parent", "ROOT must have no parent", screenId=sid)

        ids = set()
        keys_in, keys_all = [], []
        for nid, node in contents.items():
            np_ = f"{cp}.{nid}"
            if not isinstance(node, dict):
                add("error", "screen_bad_node", np_, "node is not an object", screenId=sid)
                continue
            name = resolved_name(node)
            comp = known.get(name) if name else None
            if comp is None and name in aliases:
                # The name the console saves this component under (e.g. CodeInput for Code).
                comp = known.get(aliases[name]["to"])
            if comp is None and name not in BUILTIN_COMPONENTS:
                add("error", "screen_unknown_component", f"{np_}.type",
                    f"unknown component {name!r} (not in the flow editor's components; the screen does not render "
                    "and the console fails to open it)", screenId=sid)
            props = node.get("props")
            if not isinstance(props, dict):
                add("error", "screen_bad_node", f"{np_}.props", "node has no props object", screenId=sid)
                props = {}
            if name in TEMPLATED_COMPONENTS:
                for text in strings(props):
                    for key in TEMPLATE_RE.findall(text):
                        templated.setdefault(sid, {}).setdefault(key, f"{np_}.props")
            custom = node.get("custom")
            if custom is not None and not isinstance(custom, dict):
                add("error", "screen_bad_node", f"{np_}.custom", "custom must be an object", screenId=sid)
            custom = as_dict(custom)
            submits = node_interactions(node)
            if not as_str(props.get("id")):
                # Only a submitting node's props.id is read (as its interaction id); polling uses fixed ids.
                needed = any(i not in ("polling", "polling-error") for i in submits)
                add("error" if needed else "warning", "screen_missing_prop", f"{np_}.props.id",
                    "node has no props.id (a string; the console reads it as the interaction id)", screenId=sid)

            # Tree links: children must exist and point back; a non-ROOT node must have a parent that lists it.
            children = node.get("nodes")
            if children is not None and not isinstance(children, list):
                add("error", "screen_bad_node", f"{np_}.nodes", "nodes must be a list of node ids", screenId=sid)
            children = as_list(children)
            for c in children:
                child = contents.get(c) if isinstance(c, str) else None
                if not isinstance(child, dict):
                    add("error", "screen_bad_node", f"{np_}.nodes", f"child {c!r} is not in contents", screenId=sid)
                elif child.get("parent") != nid:
                    add("error", "screen_bad_node", f"{cp}.{c}.parent",
                        f"child {c!r} of {nid!r} has parent {child.get('parent')!r}", screenId=sid)
            if nid != "ROOT":
                pid = node.get("parent")
                parent = contents.get(pid) if isinstance(pid, str) else None
                if not isinstance(parent, dict):
                    add("error", "screen_bad_node", f"{np_}.parent", f"parent {pid!r} is not in contents",
                        screenId=sid)
                elif nid not in as_list(parent.get("nodes")) and nid not in as_dict(parent.get("linkedNodes")).values():
                    add("error", "screen_bad_node", f"{np_}.parent",
                        f"parent {pid!r} does not list {nid!r} in its nodes", screenId=sid)
            if children and not node.get("isCanvas"):
                add("warning", "screen_bad_node", f"{np_}.isCanvas", "a node with children should have isCanvas: true",
                    screenId=sid)

            if comp is not None:
                if catalog.get("renders", {}).get(name, "") is None:
                    add("error", "screen_component_not_rendered", f"{np_}.type",
                        f"{name!r} is in the editor but the renderer cannot draw it (flow-components "
                        f"{catalog['generated'].get('flowComponents')}): import succeeds and the screen never shows",
                        screenId=sid)
                known_props = comp.get("knownProps")
                for prop in props if known_props else ():
                    if prop not in known_props and not prop.startswith(FREE_PROP_PREFIXES):
                        add("info", "screen_prop_unknown", f"{np_}.props.{prop}",
                            f"{name} reads no prop {prop!r} (not in its knownProps in "
                            "references/catalog/screens/components.json), so it has no effect", screenId=sid)
                for prop, info in comp.get("typedProps", {}).items():
                    value = props.get(prop)
                    if "values" in info and isinstance(value, str) and value and value not in info["values"]:
                        add("warning", "screen_prop_value", f"{np_}.props.{prop}",
                            f"{name}.{prop} is {value!r}; flow-components takes {', '.join(info['values'])}",
                            screenId=sid)
                want = comp.get("customType")
                have = custom.get("type")
                if want and have != want:
                    # A button without it loses its interaction, and the console drops its next rules on save.
                    add("error" if want in ("button", "polling") else "warning", "screen_custom_mismatch",
                        f"{np_}.custom",
                        f"{name} needs custom {{\"type\": {want!r}}} (found {have!r}); the console derives "
                        "interactions and input keys from it", screenId=sid)
                if comp["kind"] == "input" and not as_str(props.get("name")):
                    add("error", "screen_missing_prop", f"{np_}.props.name",
                        f"{name} has no props.name, so its value reaches no context key", screenId=sid)
                if comp["kind"] == "button" and not props.get("children") and not props.get("startIcon"):
                    add("warning", "screen_missing_prop", f"{np_}.props.children", f"{name} has no label (children)",
                        screenId=sid)

            for iid in submits:
                if not iid:
                    continue
                if iid in ids and iid not in ("polling", "polling-error"):
                    add("error", "screen_duplicate_interaction", f"{np_}.props.id",
                        f"interaction id {iid!r} is used by more than one component", screenId=sid)
                ids.add(iid)
            pname = as_str(props.get("name"))
            if pname:
                key = resolve_input_key(pname, version)
                keys_all.append(key)
                if custom.get("type") == "input":
                    keys_in.append(key)
            if name == "OutboundAppButton":
                key = f'[data-name="{props.get("data-name")}"]'
                if key not in keys_all:
                    keys_all.append(key)
        derived[sid] = ids
        input_keys[sid] = (keys_in, keys_all)

        listed = screen.get("interactions")
        if listed is not None and not isinstance(listed, list):
            add("error", "screen_bad_shape", f"{sp}.interactions", "interactions must be a list", screenId=sid)
        listed_ids = set()
        for j, inter in enumerate(as_list(listed)):
            iid = as_str(inter.get("id")) if isinstance(inter, dict) else None
            if not iid:
                add("error", "screen_bad_shape", f"{sp}.interactions[{j}]", "interaction has no id (a string)",
                    screenId=sid)
                continue
            listed_ids.add(iid)
            if iid not in ids:
                add("warning", "interaction_no_component", f"{sp}.interactions[{j}]",
                    f"interaction {iid!r} matches no submitting component's props.id", screenId=sid)
        listed_by_screen[sid] = listed_ids

    used = set()
    connected_by_screen = {}
    for tid, task in tasks.items():
        if not isinstance(task, dict) or task.get("type") != "screen":
            continue
        tp = f"$.contents.tasks.{tid}"
        sid = as_str(task.get("screenId"))
        if sid in unreadable:
            used.add(sid)
            continue
        if not sid or sid not in derived:
            add("error", "screen_missing", f"{tp}.screenId",
                f"screen task points at screen {task.get('screenId')!r}, which is not in screens (import accepts "
                "it; the flow fails at runtime)", taskId=tid)
            continue
        used.add(sid)
        ids = derived[sid]
        nxt = task.get("next")
        if nxt is not None and not isinstance(nxt, dict):
            add("error", "task_bad_shape", f"{tp}.next", "next must be an object", taskId=tid)
        connected = set()
        for k, rule in enumerate(as_list(as_dict(nxt).get("rules"))):
            iid = as_str(rule.get("interactionId")) if isinstance(rule, dict) else None
            connected.add(iid)
            if iid not in ids:
                add("error", "next_rule_unknown_interaction", f"{tp}.next.rules[{k}].interactionId",
                    f"rule interactionId {iid!r} matches no submitting component on screen {sid!r} "
                    f"(have: {', '.join(sorted(ids)) or 'none'})", taskId=tid, screenId=sid)
        connected_by_screen.setdefault(sid, set()).update(connected)
        listed = listed_by_screen.get(sid, set())
        for iid in sorted(ids - connected - (OPTIONAL_INTERACTIONS - listed)):
            if f"{tid}.{iid}" in shared:
                continue  # a subflow output: the parent flow connects it
            if iid == "polling-error":
                add("error", "interaction_unconnected", f"{tp}.next.rules",
                    f"screen {sid!r} lists 'polling-error' but the task has no rule for it: when the link expires "
                    "the flow fails with NextTaskNotFound. Connect it (templates go to a 'Polling expired' screen "
                    "or back to the first screen) or drop it from the screen's interactions", taskId=tid,
                    screenId=sid)
                continue
            add("error", "interaction_unconnected", f"{tp}.next.rules",
                f"interaction {iid!r} on screen {sid!r} has no next rule; pressing it fails the flow with "
                "NextTaskNotFound", taskId=tid, screenId=sid)
        keys_in, keys_all = input_keys.get(sid, ([], []))
        for field, want in (("inputKeys", keys_in), ("allInputKeys", keys_all)):
            have = task.get(field)
            if have is None:
                if field == "allInputKeys" and task.get("calculatedInputKeys") and want:
                    add("warning", "input_keys_mismatch", f"{tp}.{field}",
                        f"screen task has calculatedInputKeys but no allInputKeys: the server sends the screen only "
                        f"the inputs allInputKeys lists, so {sorted(want)} get no values from the flow; add "
                        "allInputKeys (import doesn't compute it)", taskId=tid, screenId=sid)
                continue
            if not isinstance(have, list) or not all(isinstance(k, str) for k in have):
                add("warning", "input_keys_mismatch", f"{tp}.{field}", f"{field} must be a list of strings",
                    taskId=tid, screenId=sid)
            elif sorted(map(canonical_key, have)) != sorted(map(canonical_key, want)):
                add("warning", "input_keys_mismatch", f"{tp}.{field}",
                    f"{field} {sorted(have)} differs from the screen's input names {sorted(want)}",
                    taskId=tid, screenId=sid)
        # The server sends a screen only the context keys its task lists; the console fills the list on save,
        # hand-written JSON must.
        listed_keys = {k for k in as_list(task.get("contextKeys")) if isinstance(k, str)}
        for key, where in sorted(templated.get(sid, {}).items()):
            if key.startswith(UNLISTED_PREFIXES) or key in UNLISTED_KEYS or key in listed_keys:
                continue
            add("warning", "context_key_not_listed", f"{tp}.contextKeys",
                f"screen {sid!r} shows {{{{{key}}}}} ({where}) but the task's contextKeys don't list {key!r}, so the "
                f"server doesn't send it and it renders empty; add {key!r} to contextKeys", taskId=tid, screenId=sid)

    # A connected interaction missing from screen.interactions: the MCP flow import rejects the flow; an unconnected
    # one only confuses the console.
    for i, screen in enumerate(screens):
        sid = as_str(screen.get("screenId")) if isinstance(screen, dict) else None
        if not sid or sid not in derived:
            continue
        missing = derived[sid] - listed_by_screen.get(sid, set()) - OPTIONAL_INTERACTIONS
        for iid in sorted(missing):
            connected = iid in connected_by_screen.get(sid, set())
            add("error" if connected else "warning", "interaction_not_listed", f"$.screens[{i}].interactions",
                f"component interaction {iid!r} is missing from the screen's interactions"
                + (" (the MCP import rejects a rule to it)" if connected else ""), screenId=sid)
        if sid not in used:
            add("warning", "screen_unused", f"$.screens[{i}]",
                f"no screen task uses screen {sid!r} (the console drops it on save)", screenId=sid)
    return out


def main(argv):
    as_json = "--json" in argv
    paths = [a for a in argv if a != "--json"]
    if not paths:
        print(__doc__)
        return 2
    bad = False
    results = {}
    for p in paths:
        with open(p) as f:
            flow = json.load(f)
        if isinstance(flow, dict) and "flow" in flow and "contents" not in flow:
            flow = flow["flow"]
        found = check_screens(flow)
        results[p] = found
        bad = bad or any(x["severity"] == "error" for x in found)
        if not as_json:
            for x in found:
                print(f"{p}: {x['severity']} {x['code']} {x['path']}: {x['message']}")
    if as_json:
        print(json.dumps(results, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
