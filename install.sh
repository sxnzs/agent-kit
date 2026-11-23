#!/usr/bin/env bash
# Amnesiac Agents installer. One source of truth, linked into Claude Code, Codex, OpenCode, Pi and Gemini/Antigravity.
# Cursor needs no install step: it loads the kit as a plugin (see README).
#
#   ./install.sh                 install for every host found on this machine
#   ./install.sh --all           install for all five hosts even if not found
#   ./install.sh --only=claude,pi,gemini
#   ./install.sh --dry-run       show what would change
#   ./install.sh --uninstall     remove links and merged config entries
#
# Safe by design: idempotent, existing files are moved to *.bak.<timestamp>,
# JSON configs are merged (your values win), Codex config.toml is never overwritten.
#
# Private overlay: when ${AGENT_KIT_LOCAL:-~/.config/agent-kit}/AGENTS.md or CLAUDE.md exists,
# hosts link to your copy instead of the kit's, so personal rules stay out of the repo.
set -euo pipefail

KIT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
LOCAL="${AGENT_KIT_LOCAL:-$HOME/.config/agent-kit}"
INSTRUCTIONS="$KIT/AGENTS.md"
CLAUDE_RULES="$KIT/adapters/claude/CLAUDE.md"
if [ -f "$LOCAL/AGENTS.md" ]; then INSTRUCTIONS="$LOCAL/AGENTS.md"; fi
if [ -f "$LOCAL/CLAUDE.md" ]; then CLAUDE_RULES="$LOCAL/CLAUDE.md"; fi
STAMP="$(date +%Y%m%d%H%M%S)"
DRY=0; UNINSTALL=0; FORCE_ALL=0; ONLY=""

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --all) FORCE_ALL=1 ;;
    --only=*) ONLY="${arg#--only=}" ;;
    --only) echo "use --only=claude,codex,opencode,pi,gemini"; exit 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg"; exit 2 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
run()  { if [ "$DRY" = 1 ]; then say "  would: $*"; else "$@"; fi; }
DRYFLAG=""; [ "$DRY" = 1 ] && DRYFLAG="--dry-run"

want() {  # want <host> <binary> <config dir>
  local host="$1" bin="$2" dir="$3"
  if [ -n "$ONLY" ]; then [[ ",$ONLY," == *",$host,"* ]]; return; fi
  [ "$FORCE_ALL" = 1 ] || command -v "$bin" >/dev/null 2>&1 || [ -d "$dir" ]
}

is_ours() {  # true for a link target inside the kit, the private overlay, or ~/.agents/skills
  [[ "$1" == "$KIT"* ]] || [[ "$1" == "$LOCAL"/* ]] || [ "$1" = "$HOME/.agents/skills" ]
}

link() {  # link <source> <destination>
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then say "  ok        $dst"; return; fi
  local replace_kit=0 backup=""
  if [ -L "$dst" ] && is_ours "$(readlink "$dst")"; then
    replace_kit=1
  elif [ -e "$dst" ] || [ -L "$dst" ]; then
    backup="$dst.bak.$STAMP"
  fi
  if [ "$DRY" = 1 ]; then
    if [ "$replace_kit" = 1 ]; then say "  would relink $dst"; else say "  would link $dst${backup:+ (backup existing)}"; fi
    return
  fi
  mkdir -p "$(dirname "$dst")"
  if [ "$replace_kit" = 1 ]; then rm "$dst"; fi
  if [ -n "$backup" ]; then mv "$dst" "$backup"; say "  backup    $dst -> $backup"; fi
  ln -s "$src" "$dst"; say "  linked    $dst"
}

unlink_kit() {  # remove dst only if it is one of our symlinks, restore newest backup
  local dst="$1" bak
  if [ -L "$dst" ] && is_ours "$(readlink "$dst")"; then
    run rm "$dst"; say "  removed   $dst"
    bak="$(ls -1d "$dst".bak.[0-9]* 2>/dev/null | sort | tail -n 1 || true)"
    if [ -n "$bak" ]; then run mv "$bak" "$dst"; say "  restored  $dst"; fi
  fi
}

place_copy() {  # Codex ignores symlinked rules files, so copy them with @KIT@ filled in; uninstall removes an identical copy
  local src="$1" dst="$2" rendered
  rendered="$(sed "s#@KIT@#$KIT#g" "$src")"
  if [ "$UNINSTALL" = 1 ]; then
    if [ -f "$dst" ] && [ "$rendered" = "$(cat "$dst")" ]; then run rm "$dst"; say "  removed   $dst"; fi
    return
  fi
  if [ -f "$dst" ] && [ ! -L "$dst" ] && [ "$rendered" = "$(cat "$dst")" ]; then say "  ok        $dst"; return; fi
  if [ "$DRY" = 1 ]; then say "  would copy $dst"; return; fi
  mkdir -p "$(dirname "$dst")"
  if [ -e "$dst" ] || [ -L "$dst" ]; then mv "$dst" "$dst.bak.$STAMP"; say "  backup    $dst -> $dst.bak.$STAMP"; fi
  printf '%s\n' "$rendered" > "$dst"; say "  copied    $dst"
}
place() { if [ "$UNINSTALL" = 1 ]; then unlink_kit "$2"; else link "$1" "$2"; fi; }
jmerge() { python3 "$KIT/scripts/jsonmerge.py" "$([ "$UNINSTALL" = 1 ] && echo unmerge || echo merge)" "$1" "$2" $DRYFLAG; }

link_skills() {  # link_skills <skills dir>
  local bucket s
  for bucket in "$KIT"/skills/*/; do
    [ -d "$bucket" ] || continue
    [ "$(basename "$bucket")" = "in-progress" ] && continue
    for s in "$bucket"*/; do
      [ -d "$s" ] || continue
      s="${s%/}"
      place "$s" "$1/$(basename "$s")"
    done
  done
}

# ---------------------------------------------------------------- shared
say "Shared (~/.agents)"
place "$KIT"           "$HOME/.agents/agent-kit"
place "$INSTRUCTIONS"  "$HOME/.agents/AGENTS.md"
link_skills "$HOME/.agents/skills"          # read by Codex, OpenCode and Pi
place "$KIT/bin/cm"    "$HOME/.local/bin/cm"  # per session code mode, see CODEMODE.md
[ "$UNINSTALL" = 1 ] || run chmod +x "$KIT/guard/guard.py" "$KIT/scripts/jsonmerge.py" "$KIT/scripts/check_skills.py" "$KIT/scripts/verify" "$KIT/bin/cm"

# ---------------------------------------------------------------- Claude Code
if want claude claude "$HOME/.claude"; then
  say "Claude Code"
  C="$HOME/.claude"
  link_skills "$C/skills"
  place "$KIT/adapters/claude/agents/verifier.md" "$C/agents/verifier.md"
  # Claude-only rules. A CLAUDE.md you wrote yourself is kept and only gains the import below.
  if [ "$UNINSTALL" = 1 ] || [ ! -e "$C/CLAUDE.md" ] || { [ -L "$C/CLAUDE.md" ] && is_ours "$(readlink "$C/CLAUDE.md")"; }; then
    place "$CLAUDE_RULES" "$C/CLAUDE.md"
  else
    say "  kept      $C/CLAUDE.md (yours; the kit's Claude rules are in adapters/claude/CLAUDE.md)"
  fi
  jmerge "$C/settings.json" "$KIT/adapters/claude/settings.fragment.json"
  IMPORT='@~/.agents/AGENTS.md'
  if [ "$UNINSTALL" = 1 ]; then
    if [ -f "$C/CLAUDE.md" ] && grep -qxF "$IMPORT" "$C/CLAUDE.md"; then
      # Drop the import and the blank line install added after it.
      if [ "$DRY" = 1 ]; then say "  would: drop $IMPORT from $C/CLAUDE.md"
      else
        cp "$C/CLAUDE.md" "$C/CLAUDE.md.bak.agent-kit"
        awk -v imp="$IMPORT" '
          $0 == imp { dropped = NR; next }
          dropped && NR == dropped + 1 && $0 == "" { next }
          { print }' "$C/CLAUDE.md.bak.agent-kit" > "$C/CLAUDE.md"
        say "  unimport  $C/CLAUDE.md"
      fi
    fi
  elif [ -f "$C/CLAUDE.md" ] && grep -qxF "$IMPORT" "$C/CLAUDE.md"; then
    say "  ok        $C/CLAUDE.md imports AGENTS.md"
  elif [ "$(readlink -f "$HOME/AGENTS.md" 2>/dev/null)" = "$(readlink -f "$INSTRUCTIONS")" ]; then
    # Claude Code walks up to ~/AGENTS.md from any cwd under ~; an import would load it twice.
    say "  ok        ~/AGENTS.md loads by walk up, no import needed"
  elif [ -L "$C/CLAUDE.md" ]; then
    say "  note      $CLAUDE_RULES lacks the line $IMPORT, so Claude Code will not load AGENTS.md"
  else
    run mkdir -p "$C"
    if [ "$DRY" = 1 ]; then say "  would: add $IMPORT to $C/CLAUDE.md"
    else printf '%s\n\n%s\n' "$IMPORT" "$( [ -f "$C/CLAUDE.md" ] && cat "$C/CLAUDE.md" )" > "$C/CLAUDE.md.tmp" && mv "$C/CLAUDE.md.tmp" "$C/CLAUDE.md"
         say "  import    $C/CLAUDE.md"; fi
  fi
fi

# ---------------------------------------------------------------- Codex
if want codex codex "$HOME/.codex"; then
  say "Codex"
  X="$HOME/.codex"
  place "$INSTRUCTIONS"                         "$X/AGENTS.md"
  place_copy "$KIT/adapters/codex/rules/agent-kit.rules" "$X/rules/agent-kit.rules"
  place "$KIT/adapters/codex/agents/verifier.toml"  "$X/agents/verifier.toml"
  jmerge "$X/hooks.json" "$KIT/adapters/codex/hooks.json"
  if [ "$UNINSTALL" = 0 ]; then
    if [ -f "$X/config.toml" ]; then
      say "  kept      $X/config.toml (merge keys from adapters/codex/config.toml by hand if wanted)"
    else
      run mkdir -p "$X"; run cp "$KIT/adapters/codex/config.toml" "$X/config.toml"; say "  created   $X/config.toml"
    fi
    say "  note      open Codex and approve the hook once in /hooks"
  fi
fi

# ---------------------------------------------------------------- OpenCode
if want opencode opencode "$HOME/.config/opencode"; then
  say "OpenCode"
  O="$HOME/.config/opencode"
  if grep -q '\.agents/AGENTS\.md' "$O/opencode.json" 2>/dev/null; then
    say "  kept      $O/AGENTS.md (opencode.json instructions loads the kit)"
  else
    place "$INSTRUCTIONS"                                "$O/AGENTS.md"
  fi
  place "$KIT/adapters/opencode/agents/verifier.md"       "$O/agents/verifier.md"
  place "$KIT/adapters/opencode/plugins/agent-kit-guard"    "$O/plugins/agent-kit-guard"
  if [ -f "$O/opencode.jsonc" ] && [ ! -f "$O/opencode.json" ]; then
    say "  skipped   $O/opencode.jsonc (JSONC). Merge adapters/opencode/opencode.fragment.json by hand"
  else
    jmerge "$O/opencode.json" "$KIT/adapters/opencode/opencode.fragment.json"
  fi
fi

# ---------------------------------------------------------------- Pi
if want pi pi "$HOME/.pi"; then
  say "Pi"
  P="$HOME/.pi/agent"
  place "$INSTRUCTIONS"                                "$P/AGENTS.md"
  place "$KIT/adapters/pi/extensions/agent-kit-guard.ts" "$P/extensions/agent-kit-guard.ts"
  place "$KIT/adapters/pi/prompts/verify.md"            "$P/prompts/verify.md"
fi

# ---------------------------------------------------------------- Gemini / Antigravity
if want gemini agy "$HOME/.gemini"; then
  say "Gemini / Antigravity"
  G="$HOME/.gemini/config"
  place "$HOME/.agents/skills" "$G/skills"
fi

# ---------------------------------------------------------------- check
if [ "$UNINSTALL" = 0 ] && [ "$DRY" = 0 ]; then
  say "Guard self test"
  python3 "$KIT/guard/guard.py" --test | tail -n 1
  say "Skills check"
  python3 "$KIT/scripts/check_skills.py" --check-links "$HOME/.agents/skills"
fi
say "Done."
