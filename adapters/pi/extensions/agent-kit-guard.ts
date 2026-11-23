// Amnesiac Agents guard for Pi. Installed to ~/.pi/agent/extensions/.
// Deny rules block. Ask rules open a confirm dialog, and block when there is no UI (pi -p).
// Type only import: erased at load time, so it works with either package name.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { homedir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const corePath = join(homedir(), ".agents", "agent-kit", "guard", "core.mjs");

export default async function (pi: ExtensionAPI) {
  let evaluate: ((tool: string, input: Record<string, unknown>) => { decision: string | null; reason?: string }) | undefined;
  try {
    ({ evaluate } = await import(pathToFileURL(corePath).href));
  } catch (err) {
    console.error(`agent-kit guard: could not load ${corePath} (allowing): ${err}`);
    return;
  }

  pi.on("tool_call", async (event, ctx) => {
    let decision: string | null, reason: string | undefined;
    try {
      ({ decision, reason } = evaluate!(event.toolName, (event.input ?? {}) as Record<string, unknown>));
    } catch (err) {
      // A broken policy must be visible, so treat it as an ask.
      decision = "ask";
      reason = `Guard error, so this call was not checked: ${err}`;
    }
    if (decision === "deny") {
      return { block: true, reason: `[agent-kit guard] ${reason} Do not work around it.` };
    }
    if (decision === "ask") {
      if (!ctx.hasUI) return { block: true, reason: `[agent-kit guard] ${reason} No UI to approve. Ask the user.` };
      const preview = String((event.input as any)?.command ?? (event.input as any)?.path ?? "").slice(0, 300);
      const ok = await ctx.ui.confirm("Approve this action?", `${reason}\n\n${preview}`);
      if (!ok) return { block: true, reason: `[agent-kit guard] The user declined. ${reason}` };
    }
  });
}
