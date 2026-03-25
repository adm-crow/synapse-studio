from nicegui import ui
from synapse_studio.layout import build_layout
from synapse_studio.state import state


async def _confirm(message: str, confirm_label: str = "Confirm", confirm_color: str = "negative") -> bool:
    """Show a confirmation dialog and return True if the user confirmed."""
    with ui.dialog() as dialog, ui.card().classes("q-pa-md gap-3"):
        ui.label(message).classes("text-body2")
        with ui.row().classes("justify-end gap-2 q-mt-sm"):
            ui.button("Cancel", on_click=lambda: dialog.submit(False)).props("flat dense")
            ui.button(confirm_label, on_click=lambda: dialog.submit(True)).props(
                f"color={confirm_color} dense"
            )
    return await dialog


@ui.page("/collections")
def collections_page() -> None:
    build_layout("/collections")

    with ui.column().classes("w-full q-pa-xl gap-4"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Collections").classes("text-h5")
            ui.button("Refresh", icon="refresh", on_click=lambda: ui.navigate.to("/collections")).props(
                "flat color=grey-5 dense"
            )

        # ── Load data ──────────────────────────────────────────────
        try:
            from synapse_core import list_collections, collection_stats, sources
            col_names = list_collections(state.db_path)
        except Exception as exc:
            ui.label(f"Could not load collections: {exc}").classes("text-negative")
            return

        if not col_names:
            ui.label("No collections found. Run an Ingest to get started.").classes(
                "text-grey-5 text-center q-mt-xl"
            )
            return

        # ── One expansion panel per collection ─────────────────────
        for col in col_names:
            try:
                stats = collection_stats(state.db_path, col)
                src_list = sources(state.db_path, col)
            except Exception:
                stats = None
                src_list = []

            with ui.expansion(col, icon="inventory_2").classes("w-full border rounded-lg"):
                # Stats row
                if stats:
                    with ui.row().classes("gap-8 q-pa-sm items-end"):
                        with ui.column().classes("items-center"):
                            ui.label(str(stats.total_chunks)).classes("text-h6 text-primary")
                            ui.label("chunks").classes("text-caption text-grey-5")
                        with ui.column().classes("items-center"):
                            ui.label(str(stats.total_sources)).classes("text-h6 text-primary")
                            ui.label("sources").classes("text-caption text-grey-5")
                        with ui.column().classes("items-center"):
                            ui.label(stats.embedding_model or "—").classes("text-h6 text-grey-4")
                            ui.label("embedding model").classes("text-caption text-grey-5")
                else:
                    ui.label("Stats unavailable.").classes("text-caption text-grey-5 q-pa-sm")

                ui.separator()

                # Sources list with per-source delete
                if src_list:
                    ui.label("Sources").classes("text-subtitle2 q-px-sm q-pt-sm")
                    for src in src_list:
                        with ui.row().classes("items-center justify-between w-full q-px-sm q-py-xs"):
                            ui.label(src).classes("text-caption text-grey-9 ellipsis flex-1")

                            async def delete_src(s: str = src, c: str = col) -> None:
                                if not await _confirm(
                                    f'Delete "{s}" from "{c}"?',
                                    confirm_label="Delete",
                                ):
                                    return
                                try:
                                    from synapse_core import delete_source
                                    delete_source(s, state.db_path, c)
                                    ui.notify(f"Deleted: {s}", type="positive")
                                    ui.navigate.to("/collections")
                                except Exception as exc:
                                    ui.notify(f"Error: {exc}", type="negative")

                            ui.button(icon="delete_outline", on_click=delete_src).props(
                                "flat dense color=grey-5"
                            )
                else:
                    ui.label("No sources.").classes("text-caption text-grey-6 q-pa-sm")

                ui.separator()

                # Danger zone
                with ui.row().classes("gap-2 q-pa-sm"):
                    async def purge_col(c: str = col) -> None:
                        if not await _confirm(
                            f'Purge all chunks from "{c}"? This cannot be undone.',
                            confirm_label="Purge",
                            confirm_color="orange",
                        ):
                            return
                        try:
                            from synapse_core import purge
                            purge(state.db_path, c)
                            ui.notify(f"Purged collection: {c}", type="warning")
                            ui.navigate.to("/collections")
                        except Exception as exc:
                            ui.notify(f"Error: {exc}", type="negative")

                    async def reset_col(c: str = col) -> None:
                        if not await _confirm(
                            f'Reset "{c}"? This will delete all data in this collection.',
                            confirm_label="Reset",
                        ):
                            return
                        try:
                            from synapse_core import reset
                            reset(state.db_path, c, confirm=True)
                            ui.notify(f"Reset collection: {c}", type="warning")
                            ui.navigate.to("/collections")
                        except Exception as exc:
                            ui.notify(f"Error: {exc}", type="negative")

                    ui.button("Purge", icon="cleaning_services", on_click=purge_col).props(
                        "flat color=orange dense"
                    )
                    ui.button("Reset", icon="restart_alt", on_click=reset_col).props(
                        "flat color=negative dense"
                    )
