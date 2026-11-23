// Agent Kit guard for OpenCode 2.x. Installed to ~/.config/opencode/plugins/.
// Runs as a permission "evaluate" hook, so deny and ask both go through OpenCode's own
// permission flow and win over any configured allow (an explicit configured deny is
// final and never reaches the hook). V2 loads a default export with an id and setup().
// Docs: https://opencode.ai/v2/docs/build/plugins
import { homedir } from "node:os"
import { join } from "node:path"
import { pathToFileURL } from "node:url"

type Decision = { decision: string | null; reason?: string }
type Evaluate = (tool: string, input: Record<string, unknown>) => Decision

const corePath = join(homedir(), ".agents", "agent-kit", "guard", "core.mjs")

// Permission actions mapped to the tool shape core.mjs understands.
const asInput: Record<string, (resource: string) => [string, Record<string, unknown>]> = {
  shell: (r) => ["bash", { command: r }],
  bash: (r) => ["bash", { command: r }],
  edit: (r) => ["edit", { filePath: r }],
  write: (r) => ["write", { filePath: r }],
}

function strictest(evaluate: Evaluate, action: string, resources: readonly string[]): Decision {
  const map = asInput[action]
  // Any other action is a tool name (MCP tools arrive as server_tool), checked by name.
  if (!map) return evaluate(action, {})
  let ask: Decision | undefined
  for (const r of resources) {
    const result = evaluate(...map(r))
    if (result.decision === "deny") return result
    if (result.decision === "ask") ask ??= result
  }
  return ask ?? { decision: null }
}

async function setup(ctx: any) {
  let evaluate: Evaluate | undefined
  try {
    ;({ evaluate } = await import(pathToFileURL(corePath).href))
  } catch (err) {
    console.error(`agent-kit guard: could not load ${corePath} (allowing): ${err}`)
    return
  }

  await ctx.permission.hook("evaluate", async (event: any) => {
    let result: Decision
    try {
      result = strictest(evaluate!, String(event.action ?? ""), event.resources ?? [])
    } catch (err) {
      // A broken policy must be visible, so escalate instead of allowing silently.
      event.effect = "ask"
      event.message = `[agent-kit guard] Guard error, so this call was not checked: ${err}`
      return
    }
    if (result.decision === "deny") {
      event.effect = "deny"
      event.message = `[agent-kit guard] ${result.reason} Do not work around it.`
    } else if (result.decision === "ask" && event.effect !== "deny") {
      event.effect = "ask"
      event.message = `[agent-kit guard] ${result.reason}`
    }
  })
}

export default { id: "agent-kit.guard", setup }
