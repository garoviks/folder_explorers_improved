# Accessing action_explorer from Any Device

Quick guide for continuing work on this project from different locations.

## 3 Ways to Access This Project

### 1. **This Local Machine** (Kubuntu/Debian)
Memories auto-load + full development environment

```bash
cd /home/nesha/scripts/folder_explorers_improved
claude-code
```

Memories at: `/home/nesha/.claude/projects/-home-nesha-scripts-folder-explorers-improved/memory/`

---

### 2. **Any Device via Claude Projects** (No GitHub access needed)
Browse to: https://claude.ai/projects → Open "action_explorer" project

Files uploaded:
- DEVELOPMENT.md
- action_explorer_requirements.md
- action_explorer_spec.md

Start a chat in that project and I'll have full context.

---

### 3. **Any Device via GitHub + Terminal**
```bash
git clone https://github.com/garoviks/folder_explorers_improved.git
cd folder_explorers_improved
claude-code  # or start a chat
```

---

## Quick Reference Table

| Setup | Access | Files Available | Terminal Needed |
|-------|--------|-----------------|-----------------|
| Local machine | Direct | Code + memories | Yes |
| Claude Projects | Browser | Docs (3 files) | No |
| GitHub clone | Terminal | Code + DEVELOPMENT.md | Yes |

---

## When Switching Devices

**Best practice:** Mention in chat that you're continuing action_explorer work.

Example:
> "I'm continuing work on action_explorer. Last session I was working on..."

This helps me provide better continuity even without automatic memory loading.

---

## Keeping Everything Synced

1. **Make commits** to GitHub when code changes
2. **Update DEVELOPMENT.md** when architecture changes
3. **Update Claude Project files** periodically (same 3 files)
4. **Local machine memories** update automatically daily at 1am NZST

---

## GitHub is the Source of Truth

All code lives at: **https://github.com/garoviks/folder_explorers_improved**

Always push changes there, so you can access from any device later.
