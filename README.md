# Synapse Studio

A native desktop GUI for [synapse-core](https://github.com/adm-crow/synapse) — a local-first RAG (Retrieval-Augmented Generation) library.
Built with [NiceGUI](https://nicegui.io/) (Python-native desktop window, no browser required).

> No cloud, no infrastructure. Everything runs locally on your machine.

---

## Features

| Tab | Description |
|---|---|
| **Query** | Semantic search over your ingested documents with score filtering |
| **Chat** | RAG-powered chat using your documents as context (Anthropic / OpenAI) |
| **Collections** | Browse, inspect, and manage vector collections |
| **Ingest** | Index a local folder into a collection with real-time progress |
| **Settings** | Configure database path, AI provider, embedding model, and theme |

---

## Supported file formats

`.txt` `.md` `.csv` `.pdf` `.docx` `.json` `.jsonl` `.html` `.pptx` `.xlsx` `.epub` `.odt`

Requires the `[formats]` extra of synapse-core for `.html`, `.pptx`, `.xlsx`, `.epub`, `.odt`:
```bash
pip install "synapse-core[formats]"
```

---

## Requirements

- Python 3.11+
- [synapse-core](https://github.com/adm-crow/synapse) ≥ 1.1.1

---

## Installation

```bash
pip install synapse-studio
```

Or from source:

```bash
git clone https://github.com/adm-crow/synapse-studio.git
cd synapse-studio
pip install -e .
```

---

## Usage

```bash
synapse-studio
```

The app opens as a native desktop window. On first launch, open **Settings** to configure:
- **DB path** — where the vector database is stored (default: `./synapse_db`)
- **Embedding model** — any [sentence-transformers](https://huggingface.co/models?library=sentence-transformers) model (default: `all-MiniLM-L6-v2`)
- **AI provider / model / API key** — for the Chat tab (supports Anthropic and OpenAI)

Then go to **Ingest**, select a folder, and click **Start Ingest**. Once complete, use **Query** or **Chat** to search your documents.

---

## Configuration

Settings are persisted to `synapse.toml` in the working directory.
This file is **excluded from version control** (see `.gitignore`) as it contains local paths and API keys.

---

## Embedding models

Any model from [Hugging Face sentence-transformers](https://huggingface.co/models?library=sentence-transformers&sort=downloads) works.
See also the [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) for quality benchmarks.

| Model | Dims | Notes |
|---|---|---|
| `all-MiniLM-L6-v2` | 384 | Default — fast, lightweight |
| `BAAI/bge-base-en-v1.5` | 768 | Better quality, good speed |
| `BAAI/bge-large-en-v1.5` | 1024 | Best quality, slower |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Multilingual (50+ languages) |

> ⚠️ Each collection is tied to the model used at ingest time. Do not mix models within the same collection.

---

## Related

- [synapse-core](https://github.com/adm-crow/synapse) — the underlying RAG library (CLI + Python API)

---

## License

MIT — synapse-core is licensed under Apache-2.0.
