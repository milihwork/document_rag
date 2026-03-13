#!/usr/bin/env bash
# One-time setup: clone and build llama.cpp for make llm.
# Run from project root. Idempotent: skips if already present.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

LLAMA_DIR="$REPO_ROOT/llama.cpp"
LLAMA_REPO="${LLAMA_REPO:-https://github.com/ggerganov/llama.cpp}"
BINARY="$LLAMA_DIR/build/bin/llama-server"

if [[ ! -d "$LLAMA_DIR" ]]; then
  echo "Cloning llama.cpp into $LLAMA_DIR ..."
  git clone --depth 1 "$LLAMA_REPO" "$LLAMA_DIR" || exit 1
fi

if [[ ! -x "$BINARY" ]]; then
  echo "Building llama.cpp (this may take a while) ..."
  (cd "$LLAMA_DIR" && cmake -B build && cmake --build build --config Release) || exit 1
fi

mkdir -p "$REPO_ROOT/models"
echo "Done. Place your GGUF model in ./models/ then run: make llm"
