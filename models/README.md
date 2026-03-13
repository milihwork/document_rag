# LLM models (GGUF)

Do this **once** after cloning the repo if you want to use the local LLM.

This folder is for GGUF model files used by the local LLM (llama.cpp). **Do not commit model files to git** — they are large and are ignored via `.gitignore`. The llama.cpp engine is not in the repo either; set it up with `make init-llama` once.

## Default model

The run script expects:

- **File:** `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
- Or set `MODEL_PATH=./models/your-file.gguf` when running `make llm`.

## How to get the model

1. **Recommended:** Download from [Hugging Face — TheBloke/Mistral-7B-Instruct-v0.2-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF): get the **Q4_K_M** GGUF file and place it in this folder as `mistral-7b-instruct-v0.2.Q4_K_M.gguf`.
2. **Alternative:** Use any other GGUF model and set `MODEL_PATH=./models/your-model.gguf` when you run `make llm`.

## Setup order

1. Run `make init-llama` (clones and builds llama.cpp).
2. Download the GGUF model and place it in this `models/` folder.
3. Run `make llm` to start the LLM server.
