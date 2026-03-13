#!/usr/bin/env bash
# Start the llama.cpp server with Mistral model.
# Run from project root or anywhere. Paths are relative to repo root.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

LLAMA_SERVER="${LLAMA_SERVER:-./llama.cpp/build/bin/llama-server}"
MODEL_PATH="${MODEL_PATH:-./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "Model not found at $MODEL_PATH"
  echo "Set MODEL_PATH or place your GGUF model in ./models/"
  exit 1
fi

if [[ ! -x "$LLAMA_SERVER" ]]; then
  echo "llama-server not found at $LLAMA_SERVER"
  echo "Build llama.cpp first, or set LLAMA_SERVER to your binary path"
  exit 1
fi

"$LLAMA_SERVER" -m "$MODEL_PATH" -c 2048 --port 8080
