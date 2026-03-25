# Synapse Studio

A native desktop GUI for [synapse-core](https://pypi.org/project/synapse-core/) — a local RAG / semantic-search engine.
Built with [NiceGUI](https://nicegui.io/) (Python-native desktop window, no browser required).

---

## Features

| Tab | Description |
|---|---|
| **Query** | Semantic search over your ingested documents |
| **Chat** | RAG-powered chat using your documents as context |
| **Collections** | Browse, inspect, and manage vector collections |
| **Ingest** | Index a folder of documents into a collection |
| **Settings** | Configure database path, AI provider, embedding model, and theme |

---

## Requirements

- Python 3.10+
- [synapse-core](https://pypi.org/project/synapse-core/) ≥ 1.1.1

---

## Installation

```bash
pip install synapse-studio
```

Or from source:

```bash
git clone https://github.com/your-username/synapse-studio.git
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
Recommended options:

| Model | Dims | Notes |
|---|---|---|
| `all-MiniLM-L6-v2` | 384 | Default — fast, lightweight |
| `BAAI/bge-base-en-v1.5` | 768 | Better quality, good speed |
| `BAAI/bge-large-en-v1.5` | 1024 | Best quality, slower |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Multilingual |

> ⚠️ Each collection is tied to the model used at ingest time. Do not mix models within the same collection.

---

## License

MIT
