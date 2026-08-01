#!/usr/bin/env bash
#
# NeuroSync — one-time developer setup.
#
# Git hooks live in .git/hooks/, which is not versioned, so a hook committed to
# the repo does nothing until git is told where to look. This script does that
# and verifies the toolchain.
#
#   bash scripts/setup-dev.sh
#
set -euo pipefail

GRN=$'\033[32m'; YLW=$'\033[33m'; DIM=$'\033[2m'; RST=$'\033[0m'
ok()   { printf '%s\n' "${GRN}✓${RST} $1"; }
warn() { printf '%s\n' "${YLW}!${RST} $1"; }

cd "$(git rev-parse --show-toplevel)"

# --- Hooks ----------------------------------------------------------------
git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true
ok "git hooks enabled (core.hooksPath = .githooks)"
printf '%s\n' "${DIM}  pre-commit: legacy/ freeze, artefacts, secrets, blob size, conflict markers${RST}"
printf '%s\n' "${DIM}  pre-push:   legacy/ backstop, verify_d1 + noise_probe regression gates${RST}"

# --- Credential helper ----------------------------------------------------
# `manager-core` was renamed to `manager` in Git 2.39; the stale value errors
# on every remote operation.
helper=$(git config --get credential.helper || true)
if [ "$helper" = "manager-core" ]; then
    warn "credential.helper is 'manager-core', which no longer exists in modern Git."
    printf '%s\n' "${DIM}  Fix with: git config --global credential.helper manager${RST}"
fi

# --- Backend --------------------------------------------------------------
PY="core/backend/venv/Scripts/python.exe"
[ -x "$PY" ] || PY="core/backend/venv/bin/python"
if [ -x "$PY" ]; then
    ok "backend venv found ($("$PY" --version 2>&1))"
else
    warn "no venv at core/backend/venv — create one:"
    printf '%s\n' "${DIM}  cd core/backend && python -m venv venv${RST}"
    printf '%s\n' "${DIM}  ./venv/Scripts/python.exe -m pip install -r requirements.txt${RST}"
    printf '%s\n' "${DIM}  ./venv/Scripts/python.exe -m spacy download en_core_web_sm${RST}"
fi

printf '\n%s\n' "Setup complete. Rules: /CLAUDE.md · blueprints/14_EXECUTION_RULES.md"
