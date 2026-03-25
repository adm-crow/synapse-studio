import asyncio
from nicegui import ui

NAV_PAGES = [
    ("search",      "Query",       "/"),
    ("forum",       "Chat",        "/chat"),
    ("inventory_2", "Collections", "/collections"),
    ("upload",      "Ingest",      "/ingest"),
]

SETTINGS_PAGE = ("tune", "Settings", "/settings")



def build_layout(current_path: str = "/") -> None:
    """Render the shared header and sidebar. Call at the top of every page function."""
    from synapse_studio.state import state as _state
    _dark = _state.config.get("dark_mode", False)
    _primary = _state.config.get("theme_primary_dark" if _dark else "theme_primary", "#6c5ce7")
    ui.colors(primary=_primary)
    ui.dark_mode(value=_dark)

    # Full-screen overlay shown during page transitions
    overlay = ui.element("div").style(
        "display:none; position:fixed; inset:0; background:rgba(18,18,18,0.65); "
        "z-index:9999; align-items:center; justify-content:center"
    )
    with overlay:
        ui.spinner(size="xl", color="white")

    with ui.left_drawer(fixed=True, bordered=True).classes("bg-grey-9 flex flex-col").style("width: 220px; height: 100%; overflow-x: hidden"):
        ui.space().style("height: 8px")

        # ── Embedding model status badge ───────────────────────────
        model_name = _state.config.get("embedding_model") or "all-MiniLM-L6-v2"
        short_name = model_name.split("/")[-1]  # strip org prefix if any

        with ui.row().classes("items-center gap-2 q-px-md q-pb-sm no-wrap"):
            dot = ui.element("div").style(
                "width:8px; height:8px; border-radius:50%; flex-shrink:0; "
                + ("background:#00b894" if _state.model_ready else "background:#fdcb6e")
            )
            ui.label(short_name).classes("text-caption text-grey-5 ellipsis")
            spinner = ui.spinner(size="xs", color="orange")
            spinner.set_visibility(not _state.model_ready)

        def _update_dot() -> None:
            ready = _state.model_ready
            color = "#00b894" if ready else "#fdcb6e"
            dot.style(f"width:8px; height:8px; border-radius:50%; flex-shrink:0; background:{color}")
            spinner.set_visibility(not ready)

        ui.timer(0.5, _update_dot)

        ui.separator().classes("q-mx-md q-mb-sm")

        def _nav_item(icon: str, label: str, path: str) -> None:
            active = path == current_path

            async def _nav(_e, p=path) -> None:
                overlay.style("display:flex")
                await asyncio.sleep(0)
                ui.navigate.to(p)

            with ui.row().classes(
                "items-center w-full gap-3 px-4 py-2 cursor-pointer rounded-lg no-wrap "
                + ("bg-primary text-white" if active else "text-grey-4 hover:bg-grey-8 hover:text-white")
            ).on("click", _nav):
                ui.icon(icon).classes("text-lg")
                ui.label(label).classes("text-sm")

        for icon, label, path in NAV_PAGES:
            _nav_item(icon, label, path)

        ui.space()  # pushes Settings to the bottom

        ui.separator().classes("q-mx-md")
        _nav_item(*SETTINGS_PAGE)
