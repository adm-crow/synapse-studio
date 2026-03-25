import os

# Suppress noisy warnings from sentence-transformers / HuggingFace before any import
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")


def main() -> None:
    from synapse_studio.app import run
    run()
