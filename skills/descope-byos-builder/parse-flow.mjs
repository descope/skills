#!/usr/bin/env node
// Extract the BYOS-relevant shape of a Descope flow JSON export.
// Prints: every screen task, its inputs (the real form keys), its next
// rules (interactionId → target task), its UI node summary (input `name`
// attrs — what BYOS actually sends), and subflow invocations.
//
// Usage: node parse-flow.mjs <flow.json> [more-flows.json ...]
//
// Output is plain text, intended to be pasted into the BYOS screen-map
// comment header. The fields you need for BYOS components:
//   - screen name      (map key)
//   - interactionId    (what you pass to state.next)
//   - input node name  (the form key — NOT allInputKeys)
//   - contextKeys      (what the screen reads from state.context)

import { readFileSync } from 'node:fs'
import path from 'node:path'

function summarizeNode(node) {
  const comp = node.type?.resolvedName || '?'
  const p = node.props || {}
  const bits = [comp]
  if (p.name) bits.push(`name="${p.name}"`)
  if (p.ctxKey) bits.push(`ctxKey="${p.ctxKey}"`) // prefill from state.context[ctxKey]
  if (p.label) bits.push(`label="${p.label}"`)
  if (p.type) bits.push(`t="${p.type}"`)
  if (typeof p.children === 'string') {
    bits.push(`text="${p.children.slice(0, 60).replace(/\n/g, ' ')}"`)
  }
  if (p.placeholder) bits.push(`ph="${p.placeholder}"`)
  if (p.required) bits.push('req')
  if (p['data-descope-provider']) bits.push(`prov=${p['data-descope-provider']}`)
  return bits.join(' ')
}

function isWebauthnTask(task) {
  const action = task?.action?.value || task?.actionType || ''
  const name = (task?.name || '').toLowerCase()
  return /webauthn|passkey/i.test(action) || /webauthn|passkey/.test(name)
}

function findLoggedInTaskIds(tasks) {
  const ids = new Set()
  for (const [k, t] of Object.entries(tasks)) {
    const action = t?.action?.value || t?.actionType || ''
    if (/logged-?in/i.test(action) || /logged-?in/i.test(t?.name || '')) ids.add(k)
  }
  return ids
}

// A subflow loader is "post-auth" if any path from start can reach it only
// after a logged-in action. Approximation: if any rule pointing AT this
// subflow's invoker task originates from a task whose ancestors include a
// logged-in task. Cheap heuristic: subflow loader's task key is reachable
// only via tasks whose action mentions logged-in upstream. We do a simpler
// signal: scan all next.rules; if a logged-in task routes (transitively)
// into the subflow loader, mark post-auth.
function isPostAuthSubflow(loaderKey, tasks, loggedInIds) {
  if (loggedInIds.size === 0) return false
  // BFS from each logged-in task, see if we reach loaderKey.
  const seen = new Set()
  const queue = [...loggedInIds]
  while (queue.length) {
    const cur = queue.shift()
    if (seen.has(cur)) continue
    seen.add(cur)
    if (cur === loaderKey) return true
    const rules = tasks[cur]?.next?.rules ?? []
    for (const r of rules) if (r.taskId && !seen.has(r.taskId)) queue.push(r.taskId)
  }
  return false
}

function printFlow(filePath) {
  const flow = JSON.parse(readFileSync(filePath, 'utf8'))
  const flowId = flow.flowId ?? '(unknown)'
  const startTask = flow.contents?.startTask ?? '(unknown)'

  console.log('\n═══════════════════════════════════════════════════')
  console.log(`  ${path.basename(filePath)}   flowId=${flowId}`)
  console.log(`  startTask: ${startTask}`)
  console.log('═══════════════════════════════════════════════════')

  const screensArr = flow.screens ?? []
  const byScreenId = {}
  for (const s of screensArr) if (s.screenId) byScreenId[s.screenId] = s

  const tasks = flow.contents?.tasks ?? {}

  // Shared interactions (bubble up from subflows). Signal: screen.interaction
  // is NOT defined on a task but IS in metadata.sharedInteractions.
  const shared = flow.metadata?.sharedInteractions ?? []
  if (shared.length) {
    console.log('\nShared interactions (bubble to parent flow):')
    for (const s of shared) {
      console.log(`  ${s.id}${s.label ? `  "${s.label}"` : ''}${s.type ? `  [${s.type}]` : ''}`)
    }
  }

  // Screens
  for (const [taskKey, task] of Object.entries(tasks)) {
    if (!task.screenId) continue
    const scr = byScreenId[task.screenId]
    console.log(`\n── screen task ${taskKey}: "${task.name}"`)
    console.log(`   allInputKeys: ${JSON.stringify(task.allInputKeys ?? [])}`)
    console.log(`   contextKeys:  ${JSON.stringify(task.contextKeys ?? [])}`)
    if (task.inputsMetadata) {
      for (const [k, v] of Object.entries(task.inputsMetadata)) {
        console.log(`   inputsMetadata[${k}]: key="${v.key}" display="${v.displayName}"`)
      }
    }
    if (task.componentsConditions?.length) {
      console.log(`   componentsConditions: ${task.componentsConditions.length} rule(s) (see hosted-screen hide/show logic; mirror in BYOS)`)
    }
    console.log(`   next rules (interactionId → taskId):`)
    for (const r of (task.next?.rules ?? [])) {
      const target = tasks[r.taskId]
      console.log(`     • ${r.interactionId}  →  task ${r.taskId}  "${target?.name ?? '?'}"`)
    }
    if (scr) {
      console.log(`   UI nodes (action-ish components; form key = node's "name" prop):`)
      for (const [id, node] of Object.entries(scr.contents || {})) {
        if (node.type?.resolvedName === 'Container') continue
        console.log(`     [${id.slice(0, 14).padEnd(14)}] ${summarizeNode(node)}`)
      }
    }
  }

  // WebAuthn / passkey action tasks — BYOS interactions that route here
  // are SDK-handled (the SDK runs navigator.credentials.*). BYOS code must
  // NOT call WebAuthn APIs itself — just fire state.next(interactionId).
  const webauthnTasks = []
  for (const [k, t] of Object.entries(tasks)) {
    if (isWebauthnTask(t)) webauthnTasks.push({ key: k, name: t.name, action: t?.action?.value })
  }
  if (webauthnTasks.length) {
    console.log('\n── WebAuthn action tasks (SDK runs ceremony — BYOS just fires interaction):')
    for (const w of webauthnTasks) {
      console.log(`   task ${w.key} "${w.name}"  action="${w.action ?? '?'}"`)
    }
  }

  // Subflow loaders (flagged post-auth if reachable from a logged-in task)
  const loggedInIds = findLoggedInTaskIds(tasks)
  const subflows = []
  for (const [taskKey, task] of Object.entries(tasks)) {
    if (task.arguments?.flowId?.value) {
      subflows.push({
        key: taskKey,
        name: task.name,
        flowId: task.arguments.flowId.value,
        postAuth: isPostAuthSubflow(taskKey, tasks, loggedInIds),
      })
    }
  }
  if (subflows.length) {
    console.log('\n── Subflow invocations (export these flows too!):')
    for (const s of subflows) {
      const tag = s.postAuth ? '  ⚠️ POST-AUTH PROMOTION (runs after logged-in)' : ''
      console.log(`   task ${s.key} "${s.name}" → loads "${s.flowId}"${tag}`)
    }
  }

  // Screen-name collisions within this flow (detection; cross-flow collisions
  // need multi-file input — we print per-flow and the caller merges).
  const screenNames = {}
  for (const [taskKey, task] of Object.entries(tasks)) {
    if (!task.screenId) continue
    if (!screenNames[task.name]) screenNames[task.name] = []
    screenNames[task.name].push(taskKey)
  }
  const collisions = Object.entries(screenNames).filter(([, keys]) => keys.length > 1)
  if (collisions.length) {
    console.log('\n⚠️  Screen-name collisions in this flow (BYOS needs a router):')
    for (const [name, keys] of collisions) {
      console.log(`   "${name}" → tasks ${keys.join(', ')}`)
      console.log(`     → pick a context.form.* key that differs between these tasks,`)
      console.log(`       write a <${name.replace(/\W/g, '')}Router> that dispatches.`)
    }
  }
}

function main() {
  const files = process.argv.slice(2)
  if (files.length === 0) {
    console.error('Usage: node parse-flow.mjs <flow.json> [more.json ...]')
    process.exit(1)
  }
  for (const f of files) printFlow(f)

  // Cross-flow collision detection
  if (files.length > 1) {
    const allNames = {}
    for (const f of files) {
      const flow = JSON.parse(readFileSync(f, 'utf8'))
      for (const [k, t] of Object.entries(flow.contents?.tasks ?? {})) {
        if (!t.screenId) continue
        if (!allNames[t.name]) allNames[t.name] = []
        allNames[t.name].push({ file: path.basename(f), task: k })
      }
    }
    const crossCollisions = Object.entries(allNames).filter(([, refs]) => {
      const files = new Set(refs.map((r) => r.file))
      return files.size > 1
    })
    if (crossCollisions.length) {
      console.log('\n═══════════════════════════════════════════════════')
      console.log('  Cross-flow screen-name collisions (same BYOS screen')
      console.log('  renders for multiple tasks across flows):')
      console.log('═══════════════════════════════════════════════════')
      for (const [name, refs] of crossCollisions) {
        console.log(`  "${name}":`)
        for (const r of refs) console.log(`    ${r.file} task ${r.task}`)
        console.log('    → one BYOS component handles all. Use context/form')
        console.log('      heuristic to enable/disable flow-specific buttons.')
      }
    }
  }
}

main()
