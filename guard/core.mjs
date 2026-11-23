// Amnesiac Agents guard core for JavaScript hosts (OpenCode plugin, Pi extension).
// Mirrors guard.py. Policy: ~/.agents/agent-kit/guard/policy.json (or AGENT_KIT_POLICY).
// Parity check: node guard/parity.mjs
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, normalize as normalizePath } from "node:path";

export const POLICY_PATH =
  process.env.AGENT_KIT_POLICY ?? join(homedir(), ".agents", "agent-kit", "guard", "policy.json");

const PATH_KEYS = ["file_path", "filePath", "path", "notebook_path"];
// Code-mode tools carry a whole script. Scan it with the shell rules too.
const CODE_KEYS = ["code", "script"];
// Keys that may carry an apply_patch body. File content keys are not scanned.
const PATCH_KEYS = ["input", "patch", "patchText", "command", "cmd"];
const PATCH_FILE_RE = /^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$/gm;
// Values of these keys are prose, not commands: a code mode script that writes a doc
// quoting a blocked command must not be blocked by it. Template literals holding ${}
// still contain code, so they stay as they are.
const DATA_STRING_RE = new RegExp("(\\b(?:content|newText|oldText|new_string|old_string|new_str|old_str|text|body|message|summary|prompt|markdown)\\s*:\\s*)('(?:[^'\\\\]|\\\\.)*'|\"(?:[^\"\\\\]|\\\\.)*\"|\\x60[^\\x60$]*\\x60)", "g");
const SHELL_TOOLS = new Set(["bash", "shell", "exec_command", "local_shell", "container.exec"]);
const WRITE_HINTS = ["write", "edit", "patch", "notebook"];

// Command text that is data, not commands: line continuations, commit messages,
// and heredoc bodies fed to cat or tee at the start of a command. Double quoted
// messages holding $( or a backtick still run, so they are kept, and so is a
// heredoc piped onward or captured by $( outside a commit message.
const CONTINUATION_RE = /\\\n/g;
const MESSAGE_HEREDOC_RE = /(\s(?:-m|--message)(?:=|\s+))"\$\(cat\s*<<-?\s*['"]?(\w+)['"]?[ \t]*\n(?:[\s\S]*?\n)?[ \t]*\2[ \t]*\n\s*\)"/g;
const MESSAGE_RE = /(\s(?:-m|--message)(?:=|\s+))('[^']*'|"(?:[^"\\$`]|\\.|\$(?!\())*")/g;
const HEREDOC_RE = /((?:^|[;&\n])\s*(?:cat|tee)\b[^\n|]*<<-?\s*['"]?(\w+)['"]?[^\n|]*\n)(?:[\s\S]*?\n)?([ \t]*\2[ \t]*(?=\n|$))/g;

let cached;
export function loadPolicy() {
  cached ??= JSON.parse(readFileSync(POLICY_PATH, "utf8"));
  return cached;
}

export function firstMatch(rules, texts) {
  for (const rule of rules) {
    const re = new RegExp(rule.pattern);
    for (const t of texts) {
      if (re.test(t)) return rule.name ? `${rule.reason} (rule: ${rule.name})` : rule.reason;
    }
  }
  return undefined;
}

function commandOf(input) {
  const cmd = input.command ?? input.cmd ?? "";
  return Array.isArray(cmd) ? cmd.join(" ") : String(cmd);
}

export function normalize(cmd) {
  return cmd
    .replace(CONTINUATION_RE, " ")
    .replace(MESSAGE_HEREDOC_RE, "$1MSG")
    .replace(MESSAGE_RE, "$1MSG")
    .replace(HEREDOC_RE, "$1$3");
}

// A script body: normalize it, then blank the string values of data keys.
export function normalizeCode(code) {
  return normalize(code.replace(DATA_STRING_RE, '$1""'));
}

const stringsIn = (v) => (typeof v === "string" ? [v] : Array.isArray(v) ? v.filter((x) => typeof x === "string") : []);
const cleanPath = (p) => normalizePath(p === "~" ? homedir() : p.startsWith("~/") ? join(homedir(), p.slice(2)) : p);

function filePaths(input) {
  const found = PATH_KEYS.filter((k) => typeof input[k] === "string" && input[k]).map((k) => input[k]);
  if (Array.isArray(input.edits)) {
    for (const e of input.edits) {
      if (e && typeof e === "object") {
        for (const k of PATH_KEYS) if (typeof e[k] === "string" && e[k]) found.push(e[k]);
      }
    }
  }
  return found.map(cleanPath);
}

function patchPaths(input) {
  const found = [];
  for (const k of PATCH_KEYS) {
    for (const v of stringsIn(input[k])) {
      if (v.includes("*** ")) for (const m of v.matchAll(PATCH_FILE_RE)) found.push(m[1].trim());
    }
  }
  return found.map(cleanPath);
}

/** @returns {{decision: "deny" | "ask" | null, reason?: string}} */
export function evaluate(toolName, input = {}) {
  const policy = loadPolicy();
  input ??= {};
  const name = String(toolName ?? "").toLowerCase();
  let cmd = null;
  if (SHELL_TOOLS.has(name) || "command" in input || "cmd" in input) cmd = normalize(commandOf(input));
  const cmds = (cmd ? [cmd] : []).concat(CODE_KEYS.filter((k) => typeof input[k] === "string").map((k) => normalizeCode(input[k])));
  let paths = patchPaths(input);
  if (WRITE_HINTS.some((k) => name.includes(k))) paths = paths.concat(filePaths(input));
  const checks = [
    ["deny", policy.bash.deny, cmds],
    ["deny", policy.paths.deny_write, paths],
    ["deny", policy.tools?.deny ?? [], name ? [name] : []],
    ["ask", policy.bash.ask, cmds],
    ["ask", policy.paths.ask_write, paths],
    ["ask", policy.tools?.ask ?? [], name ? [name] : []],
  ];
  for (const [decision, rules, texts] of checks) {
    const reason = firstMatch(rules, texts);
    if (reason) return { decision, reason };
  }
  return { decision: null };
}
