Git & GitHub Context + git_menu.bat Command Guide
1) What are Git and GitHub?

Git: a distributed version control system. It tracks file changes, lets you branch, merge, and collaborate safely.

GitHub: a cloud platform that hosts Git repositories, issues/PRs, CI/CD, and collaboration tools.

Core workflow

Edit code locally

git add → stage changes

git commit → save a snapshot

git push → upload to GitHub

git pull → download from GitHub

2) Essential Git Commands (with common options)
Repository basics
git init                     # Create a new repo in current folder
git clone <url>              # Copy a remote repo locally
git status                   # Show changed/unstaged/untracked files
git add .                    # Stage all changes
git commit -m "message"      # Commit staged changes
git log --oneline            # Compact history
git diff                     # Show unstaged diffs
git diff --cached            # Show staged diffs

Remotes & synchronization
git remote -v                # List remotes
git remote add origin <url>  # Set main remote
git fetch origin             # Fetch remote refs
git pull origin main         # Merge remote changes into local
git push origin main         # Push local commits to GitHub

Branching
git branch                   # List branches
git branch <name>            # Create branch
git checkout <name>          # Switch branch (older syntax)
git switch <name>            # Switch branch (newer syntax)
git checkout -b <name>       # Create + switch
git merge <name>             # Merge <name> into current branch
git log --graph --oneline --all  # Visual history

Cleanup & ignore
git clean -n                 # Preview untracked files to delete
git clean -f                 # Delete untracked files
git gc                       # Optimize repo storage
# .gitignore: patterns to exclude from Git (e.g., secrets, build, logs)

Config & credentials
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --list            # View config

3) GitHub Collaboration Concepts

Pull Request (PR): propose, review, and merge changes.

Issues: track tasks/bugs/enhancements.

Actions (CI/CD): automate tests/builds/deploys.

Protected branches: require reviews or passing checks before merge.

4) .gitignore Quick Patterns
# Python
__pycache__/
*.pyc

# Logs
logs/
*.log

# Envs / Secrets
.env
config/*.json

# OS/IDE
.DS_Store
Thumbs.db
.vscode/
.idea/

5) git_menu.bat – What it does and why

This batch script provides an interactive menu to run common Git operations reliably and quickly, reducing mistakes for daily workflows.

5.1 How to run

Double click git_menu.bat or run from terminal:

.\git_menu.bat

5.2 Menu options & underlying commands
Option	Purpose	What it runs (simplified)
1) Configure Git	Set your identity for commits	git config --global user.name/email
2) Initialize repo & connect	Create .git, set origin, create .gitignore, first push	git init, git remote add origin <url>, git add ., git commit, git push -u origin main
3) Automatic push	Stage, commit with auto-message, push to main	git add ., git commit -m "Auto-update …", git push origin main
4) Push with custom message	Same as 3 but message entered by you	git add ., git commit -m "<your msg>", git push origin main
5) Quick interactive commit	Choose commit type (feat/fix/docs/…), enter description, optional push	git add ., git commit -m "<type>: <desc>", git push (optional)
6) Automatic pull	Fetch, stash local changes if needed, pull, restore stash	git fetch, git stash push, git pull, git stash pop
7) Full sync	Pull remote, then stage+commit+push local changes	git fetch/pull, git add ., git commit -m "Sync …", git push
8) Detailed status	Show repository state, remotes, last commits, sync stats	git status, git remote -v, git log -10, git branch --show-current, git rev-list …
9) Commit history	Different views: simple, detailed, graph, by author/date	git log --oneline/--stat/--graph, git shortlog -sn
10) Differences	Show diffs (working dir, staged, vs remote)	git diff, git diff --cached, git diff HEAD, git diff origin/main
11) Cleanup	Remove untracked files/dirs and optimize repo	git clean -f/-fd, git gc
12) Create/Update .gitignore	Generate a comprehensive .gitignore for the project	Writes patterns to .gitignore
13) Configure credentials	Set/update user.name and user.email	git config --global user.name/email, git config --list
14) Full workflow	Pull → you work → add+commit+push	Combines 6 + status + interactive commit/push
15) Emergency backup	Commit & push everything with timestamp	git add -A, git commit -m "EMERGENCY BACKUP …", git push
0) Exit	Exit the menu	—
5.3 Smart helpers inside the script

Quick repo health: git status --porcelain to detect pending changes.

Sync counters: git rev-list HEAD..origin/main --count (behind) and origin/main..HEAD (ahead).

Auto-stash on pull: Prevents conflicts when you have local modifications.

Safety prompts: Confirms destructive actions (cleanup) and shows previews (git clean -n).

Consistent remote: Ensures origin is set to https://github.com/codedosecodes/generator_MCP.git.

6) Recommended Daily Routine (with the menu)

[6] Pull to sync before you start.

Work normally (edit/test).

[5] Quick commit or [4] Push with custom message.

If in a hurry, [15] Emergency backup.

7) Troubleshooting Tips

“Detached HEAD”: switch back to a branch: git switch main.

Rejected push: pull first ([6]), resolve conflicts, then push.

Credentials prompt loops: reconfigure with [13]; ensure you’re logged into GitHub and have access.

Ignored files tracked: git rm --cached <file> then commit.

8) Security Notes

Never commit secrets: API keys, tokens, passwords. Keep them in .env or encrypted stores; ensure .gitignore excludes them.

Use branch protection on main for production projects (reviews, CI checks).