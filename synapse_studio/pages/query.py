from nicegui import ui
from synapse_studio.layout import build_layout
from synapse_studio.state import state


def _load_collections() -> list[str]:
    try:
        from synapse_core import list_collections
        return list_collections(state.db_path)
    except Exception:
        return []


@ui.page("/")
def query_page() -> None:
    build_layout("/")

    with ui.column().classes("w-full q-pa-xl gap-4"):
        ui.label("Query").classes("text-h5")

        # ── Controls ──────────────────────────────────────────────
        collections = _load_collections()

        with ui.row().classes("w-full gap-4 items-end"):
            collection_select = ui.select(
                options=collections,
                value=collections[0] if collections else None,
                label="Collection",
            ).classes("flex-1")
            n_results = ui.number("Results", value=5, min=1, max=100).classes("w-28")
            min_score = ui.number("Min score", value=0.0, min=0.0, max=1.0, step=0.05, format="%.2f").classes("w-28")
            ui.button(
                icon="refresh",
                on_click=lambda: ui.navigate.to("/"),
            ).props("flat color=grey-5 dense").tooltip("Refresh collections")

        query_input = ui.textarea(
            label="Query",
            placeholder="Enter your search query…",
        ).classes("w-full").props("autogrow rows=3")

        results_column = ui.column().classes("w-full gap-3")

        # ── Search action ──────────────────────────────────────────
        async def run_query() -> None:
            text = query_input.value.strip()
            if not text:
                ui.notify("Please enter a query.", type="warning")
                return

            results_column.clear()
            with results_column:
                ui.spinner(size="lg")

            try:
                from synapse_core import query, collection_stats
                col_name = collection_select.value or state.collection_name
                try:
                    col_model = collection_stats(state.db_path, col_name).embedding_model or None
                except Exception:
                    col_model = None
                results = query(
                    text=text,
                    db_path=state.db_path,
                    collection_name=col_name,
                    n_results=int(n_results.value),
                    min_score=float(min_score.value),
                    embedding_model=col_model,
                )
            except Exception as exc:
                results_column.clear()
                with results_column:
                    ui.notify(f"Error: {exc}", type="negative")
                return

            results_column.clear()
            with results_column:
                if not results:
                    ui.label("No results found.").classes("text-grey-5 text-center q-mt-lg")
                    return

                ui.label(f"{len(results)} result(s)").classes("text-caption text-grey-5")

                for r in results:
                    with ui.card().classes("w-full"):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(r["source"]).classes("text-caption text-grey-5")
                            ui.badge(f"{r['score']:.2f}").props("color=primary rounded")
                        ui.separator()
                        ui.label(r["text"]).classes("text-body2")
                        if r["doc_title"]:
                            ui.label(r["doc_title"]).classes("text-caption text-grey-6 q-mt-xs")

        query_input.on("keydown.ctrl.enter", run_query)
        with ui.row().classes("items-center gap-3"):
            ui.button("Search", icon="search", on_click=run_query).props("color=primary")
            ui.label("Ctrl+Enter to search").classes("text-caption text-grey-5")

        # Reload collections if db_path was just configured
        if not collections:
            ui.label(
                "No collections found. Check your db_path in Settings or run an Ingest first."
            ).classes("text-caption text-grey-5")
