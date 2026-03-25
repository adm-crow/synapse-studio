import asyncio
import sys
from nicegui import ui, app as nicegui_app
from synapse_studio.state import state


def _exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """Suppress the noisy Windows ConnectionResetError on window close."""
    exc = context.get("exception")
    if isinstance(exc, (ConnectionResetError, OSError)) and sys.platform == "win32":
        return
    loop.default_exception_handler(context)


async def _warmup() -> None:
    """Load the embedding model into memory at startup so the first query is instant."""
    try:
        from synapse_core import query
        await asyncio.to_thread(
            query,
            text="warmup",
            db_path=state.db_path,
            collection_name=state.collection_name,
            n_results=1,
        )
    except Exception:
        pass  # db may not exist yet — that's fine, model still gets loaded
    finally:
        state.model_ready = True


_WINDOW_SIZE = (1600, 960)
_PORT = 8765


def run() -> None:
    from synapse_studio.pages import query, chat, collections, ingest, settings  # noqa: F401

    nicegui_app.on_startup(_warmup)
    nicegui_app.on_startup(lambda: asyncio.get_event_loop().set_exception_handler(_exception_handler))

    ui.run(
        native=True,
        title="Synapse Studio",
        window_size=_WINDOW_SIZE,
        reload=False,
        port=_PORT,
        show=False,
    )
