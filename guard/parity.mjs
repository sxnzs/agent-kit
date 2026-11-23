// Runs guard.py's self test cases through core.mjs and reports any case where they disagree.
//   node guard/parity.mjs
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
process.env.AGENT_KIT_POLICY ??= join(here, "policy.json");
const { evaluate } = await import("./core.mjs");

const cases = JSON.parse(execFileSync("python3", ["-I", join(here, "guard.py"), "--cases"], { encoding: "utf8" }));

// Every pattern must compile in JavaScript as well as in Python, so a policy edit cannot poison one host.
const policy = JSON.parse(await import("node:fs").then((fs) => fs.readFileSync(process.env.AGENT_KIT_POLICY, "utf8")));
let failures = 0;
for (const [group, rules] of Object.entries(policy).flatMap(([k, v]) => Object.entries(v).map(([g, r]) => [`${k}.${g}`, r]))) {
  if (!Array.isArray(rules)) continue;
  for (const rule of rules) {
    try {
      new RegExp(rule.pattern);
    } catch (err) {
      failures++;
      console.log(`FAIL ${group} "${rule.name}": JavaScript cannot compile the pattern: ${err.message}`);
    }
  }
}
for (const [tool, input, expected] of cases) {
  const got = evaluate(tool, input).decision;
  if (got !== expected) {
    failures++;
    console.log(`FAIL ${tool} ${JSON.stringify(input).slice(0, 70)} -> ${got} (expected ${expected})`);
  }
}
console.log(`${cases.length - failures}/${cases.length} match`);
process.exit(failures ? 1 : 0);
