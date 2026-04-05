# Action Explorer — How to Access & Continue Development

Your setup is complete. Choose your access method below based on your current device and preferences.

---

## 🚀 Quick Access (Pick One)

### Option A: Claude Projects (Browser, Easiest)
**Best for:** Quick edits, reference checking, planning  
**No setup needed**

1. Open https://claude.ai/projects
2. Select **"action_explorer"** project
3. Start chatting — I have full context of all 3 docs + spec

**Advantages:**
- ✅ Zero setup
- ✅ Works on any device with a browser
- ✅ I can see DEVELOPMENT.md, requirements, and spec instantly
- ✅ Direct access to your uploaded files

**Limitations:**
- ❌ No direct filesystem access
- ❌ No git operations
- ❌ Code changes require manual copy/paste

---

### Option B: Local Terminal (Full Power)
**Best for:** Full development, running the server, testing  
**Requires:** SSH key setup (see below)

```bash
# First time only: Set up SSH key (see "SSH Setup" section below)

# Then: Clone and work
git clone git@github.com:garoviks/folder_explorers_improved.git
cd folder_explorers_improved

# Start the server
python3 action_explorer.py

# Open browser to http://localhost:8123/
```

**Advantages:**
- ✅ Full code editing with your editor (VS Code, vim, etc.)
- ✅ Run the server locally and test immediately
- ✅ Git operations (commit, push, pull)
- ✅ Direct filesystem access to comic collections

**Requires:**
- Git installed
- SSH key configured (instructions below)
- Python 3.10+
- System tools: `unrar`, `unzip`, `zip`

---

### Option C: Claude Code Terminal (Hybrid)
**Best for:** Code edits + terminal commands without leaving Claude  
**Requires:** SSH key setup

1. Open https://claude.ai and start a new chat
2. Ask me to use **Claude Code** (cmd-line tool for running bash)
3. I'll clone the repo, edit files, and run tests directly

```bash
# Example: I can run this for you
git clone git@github.com:garoviks/folder_explorers_improved.git
cd folder_explorers_improved
python3 action_explorer.py --help
```

**Advantages:**
- ✅ Chat interface + terminal in one place
- ✅ I can edit code and explain changes live
- ✅ Perfect for planning + execution combo

**Limitations:**
- ⚠️ Terminal output limited to current session (no persistent server)

---

## 🔐 SSH Key Setup (One-Time, Required for Options B & C)

If you've never used GitHub SSH before, follow these steps **once**. After that, all git operations work seamlessly.

### Step 1: Check if you already have an SSH key

```bash
ls -la ~/.ssh/
```

**If you see `id_rsa` and `id_rsa.pub`:** Skip to Step 3.  
**If directory is empty or missing:** Continue to Step 2.

---

### Step 2: Generate a new SSH key

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

**Prompts you'll see:**

```
Enter file in which to save the key (/home/youruser/.ssh/id_rsa): [Press ENTER]
Enter passphrase (empty for no passphrase): [Type a strong passphrase or press ENTER for none]
Enter same passphrase again: [Repeat passphrase]
```

**Recommendations:**
- Press `ENTER` for all prompts to use defaults
- Or set a passphrase (extra security, but you'll type it each git push)

**Expected output:**
```
Your identification has been saved in /home/youruser/.ssh/id_rsa
Your public key has been saved in /home/youruser/.ssh/id_rsa.pub
The key fingerprint is: SHA256:XXXXXXXXXX...
```

---

### Step 3: Copy your public key to clipboard

```bash
cat ~/.ssh/id_rsa.pub
```

**Output example:**
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDXx7k8... your_email@example.com
```

**Copy the entire output** (from `ssh-rsa` to `your_email@example.com`).

---

### Step 4: Add key to GitHub

1. Open https://github.com/settings/keys (or Settings → SSH and GPG keys)
2. Click **"New SSH key"**
3. **Title:** `action_explorer (Kubuntu)` (or your machine name)
4. **Key type:** Authentication key
5. **Key:** Paste what you copied in Step 3
6. Click **"Add SSH key"**

---

### Step 5: Test the connection

```bash
ssh -T git@github.com
```

**If successful, you'll see:**
```
Hi @garoviks! You've successfully authenticated, but GitHub does not provide shell access.
```

**If it fails:**
- Check your email in Step 2 matches your GitHub email
- Verify the key was pasted correctly (no extra spaces)
- Try `ssh -v -T git@github.com` for debugging

---

### Step 6: Configure Git (optional but recommended)

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

---

## 📚 Understanding Your Documentation

You have three files working together:

| File | Purpose | When to Use |
|------|---------|-----------|
| **DEVELOPMENT.md** | Development reference guide, version history, architecture overview | During coding, understanding the structure |
| **action_explorer_spec.md** | Complete technical spec for implementing/re-creating the app | When building new features, or if rewriting |
| **action_explorer_requirements.md** | User-facing requirements, features, UX specifications | Before coding a feature, understanding pain points |

---

## 🔄 Common Workflows

### Scenario 1: I'm on my Kubuntu machine and want to code

```bash
# SSH key already set up from above

git clone git@github.com:garoviks/folder_explorers_improved.git
cd folder_explorers_improved

# Edit action_explorer_v13.py (or the active version)
nano action_explorer.py

# Test it
python3 action_explorer.py /path/to/comics

# Commit and push
git add .
git commit -m "Fix: parse_filename handles (001) format"
git push origin main
```

**Reference:** See DEVELOPMENT.md § "Making Changes" for version naming convention.

---

### Scenario 2: I'm on another device (laptop, work computer) and want to continue

**Option A — Use Claude Projects:**
1. Go to https://claude.ai/projects → "action_explorer"
2. Ask me: "What's the current status? What should I work on next?"
3. I'll have instant context from all docs

**Option B — Clone from GitHub:**
```bash
git clone git@github.com:garoviks/folder_explorers_improved.git
cd folder_explorers_improved

# Latest code is there
python3 action_explorer.py
```

---

### Scenario 3: I want to check requirements while coding

**Keep two browser tabs open:**
1. Tab 1: GitHub repo (or local code editor)
2. Tab 2: Claude Projects → "action_explorer" → ask me to summarize requirements

Or reference directly:
- UX questions? → See **action_explorer_requirements.md**
- Implementation details? → See **action_explorer_spec.md**
- Architecture/version info? → See **DEVELOPMENT.md**

---

### Scenario 4: I want to test the local server

```bash
cd folder_explorers_improved

# Start server
python3 action_explorer.py /path/to/your/comics

# Open in Firefox
firefox http://localhost:8123/

# Check output in terminal as you use the UI
# Stop with: Ctrl+C
```

**Troubleshooting:**
- Port 8123 in use? Change the line `PORT = 8123` in `action_explorer.py`
- Missing `unrar`? Install: `sudo apt install unrar`
- Missing `zip`? Install: `sudo apt install zip`

---

## 🧪 Development Checklist

Before committing a change, review this from **DEVELOPMENT.md**:

- [ ] Directory listing displays correctly (folders first, alphabetical)
- [ ] Volume detection works (auto-deselect warning shown)
- [ ] Select/Deselect All button toggles correctly
- [ ] Rubber-band selection works, respects auto-scroll
- [ ] CBZ creation with 2+ files succeeds
- [ ] CBZ creation with >6 files shows confirmation dialog
- [ ] Mixed series detection blocks creation
- [ ] Rename button works for files and folders
- [ ] CSV scan completes without errors
- [ ] Scroll restoration highlights correct folder on Back
- [ ] Page reloads after successful CBZ creation (10s countdown)
- [ ] Errors don't auto-reload, keep output visible

---

## 📋 System Requirements

### On Your Kubuntu/Debian Machine

```bash
# Python 3.10+
python3 --version

# System tools (install if missing)
sudo apt install unrar unzip zip git

# Verify installations
unrar -v
unzip -v
zip -v
```

### Browser
- Firefox (recommended for Linux testing)
- Any modern browser works (Chrome, Edge, etc.)

---

## 🔗 Quick Links

- **GitHub Repo:** https://github.com/garoviks/folder_explorers_improved
- **Claude Projects:** https://claude.ai/projects → "action_explorer"
- **Local Server (when running):** http://localhost:8123/
- **GitHub SSH Keys:** https://github.com/settings/keys

---

## 💡 Pro Tips

### Tip 1: Keep SSH key safe
```bash
# Verify permissions (should be 600)
ls -l ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa  # If needed
```

### Tip 2: Push after every feature
```bash
git status          # See what changed
git diff            # Review changes
git add .
git commit -m "Feature: your description"
git push origin main
```

This way, you can pull from any device later.

### Tip 3: Use Claude Projects for planning
Before writing code:
1. Open Claude Projects → "action_explorer"
2. Describe what you want to build
3. I'll check the spec and requirements
4. Get a detailed plan before you start

### Tip 4: Version your changes
Per **DEVELOPMENT.md** naming convention:
- Active version: `action_explorer.py`
- Testing new feature? Create: `action_explorer_v13.py`
- Only move to `action_explorer.py` after testing

---

## ❓ Troubleshooting

### SSH key not working
```bash
# Debug
ssh -v -T git@github.com

# Check key is in agent
ssh-add -l

# Add key to agent (if missing)
ssh-add ~/.ssh/id_rsa
```

### Can't clone repo
- Verify you've added the public key to GitHub (Step 4 above)
- Wait 1-2 minutes after adding key (GitHub syncs)
- Try again: `git clone git@github.com:garoviks/folder_explorers_improved.git`

### Server won't start
```bash
# Check Python version
python3 --version  # Must be 3.10+

# Check system dependencies
which unrar unzip zip

# Check port is free
sudo lsof -i :8123
# If in use, kill it: sudo kill -9 <PID>
```

### Changes to `action_explorer.py` not reflected
- Server caches Python modules
- Stop server: `Ctrl+C`
- Start again: `python3 action_explorer.py /path`

---

## 📞 Next Steps

1. **Choose your access method** (A, B, or C above)
2. **If using B or C:** Set up SSH key using the steps in this guide
3. **Start developing** — Reference DEVELOPMENT.md for architecture details
4. **Commit regularly** — Use Git to track progress
5. **Use Claude Projects** — For planning and requirements checking

---

**Last Updated:** 2026-04-05  
**Current Version:** action_explorer v12  
**Repository:** https://github.com/garoviks/folder_explorers_improved
