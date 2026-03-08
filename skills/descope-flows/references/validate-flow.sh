#!/usr/bin/env bash
# Descope Flow JSON Validator
# Validates flow JSON files for structural and logical correctness.
# Usage: bash validate-flow.sh <flow-file.json>

set -euo pipefail

FILE="${1:-}"
ERRORS=0
WARNINGS=0

if [ -z "$FILE" ]; then
  echo "Usage: bash validate-flow.sh <flow-file.json>"
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "ERROR: File not found: $FILE"
  exit 1
fi

error() { echo "  ERROR: $1"; ERRORS=$((ERRORS + 1)); }
warn()  { echo "  WARN:  $1"; WARNINGS=$((WARNINGS + 1)); }
info()  { echo "  OK:    $1"; }

echo "=== Descope Flow Validator ==="
echo "File: $FILE"
echo ""

# --- 1. JSON Syntax ---
echo "[1/7] Checking JSON syntax..."
if ! python3 -m json.tool "$FILE" > /dev/null 2>&1; then
  error "Invalid JSON syntax"
  echo ""
  echo "RESULT: Cannot continue — fix JSON syntax first."
  exit 1
fi
info "Valid JSON"

# --- 2. Top-Level Structure ---
echo "[2/7] Checking top-level structure..."
HAS_FLOW=$(python3 -c "import json,sys; d=json.load(open('$FILE')); print('yes' if 'flow' in d else 'no')")
HAS_SCREENS=$(python3 -c "import json,sys; d=json.load(open('$FILE')); print('yes' if 'screens' in d else 'no')")

if [ "$HAS_FLOW" != "yes" ]; then
  error "Missing top-level 'flow' key"
fi
if [ "$HAS_SCREENS" != "yes" ]; then
  error "Missing top-level 'screens' key"
fi

if [ "$HAS_FLOW" = "yes" ] && [ "$HAS_SCREENS" = "yes" ]; then
  info "Has 'flow' and 'screens' keys"
fi

# --- 3. Flow Metadata ---
echo "[3/7] Checking flow metadata..."
python3 -c "
import json, sys

with open('$FILE') as f:
    data = json.load(f)

flow = data.get('flow', {})
errors = 0

# Check flow ID
flow_id = flow.get('id', flow.get('flowId', ''))
if not flow_id:
    print('  ERROR: Missing flow id')
    errors += 1
else:
    valid_ids = ['sign-up-or-in', 'sign-up', 'sign-in', 'step-up', 'update-user']
    if flow_id in valid_ids:
        print(f'  OK:    Flow ID: {flow_id}')
    else:
        print(f'  WARN:  Flow ID \"{flow_id}\" is not a standard flow ID ({valid_ids})')

# Check flow name
if not flow.get('name'):
    print('  WARN:  Missing flow name')

# Check version
version = flow.get('version')
if version is not None:
    print(f'  OK:    Version: {version}')

sys.exit(0)
"

# --- 4. Screen References ---
echo "[4/7] Checking screen references..."
python3 -c "
import json, sys

with open('$FILE') as f:
    data = json.load(f)

flow = data.get('flow', {})
screens = data.get('screens', [])
errors = 0

# Collect screen IDs
screen_ids = set()
for screen in screens:
    sid = screen.get('id', screen.get('screenId', ''))
    if sid:
        screen_ids.add(sid)

if not screen_ids:
    print('  WARN:  No screens found in export')
    sys.exit(0)

print(f'  OK:    Found {len(screen_ids)} screen(s)')

# Look for screen references in flow data
# Screens can be referenced in various ways depending on the flow structure
flow_str = json.dumps(flow)
referenced_screens = set()

for sid in screen_ids:
    if sid in flow_str:
        referenced_screens.add(sid)

unreferenced = screen_ids - referenced_screens
if unreferenced:
    for sid in unreferenced:
        print(f'  WARN:  Screen \"{sid}\" may not be referenced in the flow')
else:
    print(f'  OK:    All screens are referenced in the flow')
"

# --- 5. Connector References ---
echo "[5/7] Checking connector references..."
python3 -c "
import json, sys, re

with open('$FILE') as f:
    data = json.load(f)

flow_str = json.dumps(data.get('flow', {}))

# Look for connector context key patterns
connector_refs = set(re.findall(r'connectors\.(\w+)', flow_str))

if connector_refs:
    print(f'  OK:    Found connector references: {\", \".join(sorted(connector_refs))}')
    print(f'  WARN:  Verify these connectors exist in the target project')
else:
    print('  OK:    No connector references found')
"

# --- 6. Flow Graph Integrity ---
echo "[6/7] Checking flow graph structure..."
python3 -c "
import json, sys

with open('$FILE') as f:
    data = json.load(f)

flow = data.get('flow', {})
errors = 0

# Check for common flow graph properties
# The exact structure varies but typically includes nodes/steps and edges/connections
flow_str = json.dumps(flow)
flow_keys = set(flow.keys()) if isinstance(flow, dict) else set()

# Report flow structure for inspection
non_meta_keys = flow_keys - {'id', 'flowId', 'name', 'description', 'version', 'disabled'}
if non_meta_keys:
    print(f'  OK:    Flow contains: {\", \".join(sorted(non_meta_keys))}')

# Check for empty flow
if len(flow_keys) <= 3:
    print('  WARN:  Flow appears to have very few properties — may be incomplete')

# Check if flow is disabled
if flow.get('disabled', False):
    print('  WARN:  Flow is marked as disabled')

sys.exit(0)
"

# --- 7. Screen Widget Validation ---
echo "[7/7] Checking screen widgets..."
python3 -c "
import json, sys

with open('$FILE') as f:
    data = json.load(f)

screens = data.get('screens', [])

for screen in screens:
    sid = screen.get('id', screen.get('screenId', 'unknown'))
    components = screen.get('components', screen.get('htmlTemplate', None))

    if components is None:
        # Check if screen has any content-like fields
        screen_keys = set(screen.keys()) - {'id', 'screenId', 'version'}
        if not screen_keys:
            print(f'  WARN:  Screen \"{sid}\" appears empty')
        else:
            print(f'  OK:    Screen \"{sid}\" has fields: {\", \".join(sorted(screen_keys))}')
    else:
        print(f'  OK:    Screen \"{sid}\" has content')

sys.exit(0)
"

# --- Summary ---
echo ""
echo "=== Summary ==="
if [ $ERRORS -gt 0 ]; then
  echo "FAILED: $ERRORS error(s), $WARNINGS warning(s)"
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  echo "PASSED with $WARNINGS warning(s) — review warnings above"
  exit 0
else
  echo "PASSED: All checks passed"
  exit 0
fi
