import asyncio
from nicegui import ui
from synapse_studio.layout import build_layout
from synapse_studio.state import state


@ui.page("/ingest")
def ingest_page() -> None:
    build_layout("/ingest")

    with ui.column().classes("w-full q-pa-xl gap-4"):
        ui.label("Ingest").classes("text-h5")

        # ── Options ────────────────────────────────────────────────
        async def browse_directory() -> None:
            import subprocess
            initial = (source_input.value or str(state.cwd)).replace("\\", "/")
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f"$d.Description = 'Select source directory'; "
                f"$d.SelectedPath = '{initial}'; "
                "$d.ShowNewFolderButton = $true; "
                "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }"
            )
            result = await asyncio.to_thread(
                subprocess.run,
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                capture_output=True,
                text=True,
            )
            path = result.stdout.strip()
            if path:
                source_input.set_value(path)

        with ui.row().classes("w-full items-end gap-2"):
            source_input = ui.input(
                label="Source directory",
                placeholder=str(state.cwd),
                value=str(state.cwd),
            ).classes("flex-1")
            ui.button(icon="folder_open", on_click=browse_directory).props("flat color=grey-5 dense").style("margin-bottom: 4px")

        with ui.row().classes("w-full gap-4"):
            collection_input = ui.input(
                label="Collection name",
                value=state.collection_name,
            ).classes("flex-1")
            db_path_input = ui.input(
                label="DB path",
                value=state.db_path,
            ).classes("flex-1")

        embed_model = state.config.get("embedding_model") or "all-MiniLM-L6-v2"
        embed_suffix = embed_model.split("/")[-1]  # strip org prefix

        def _update_collection_name(checked: bool) -> None:
            base = collection_input.value
            if checked:
                if not base.endswith(f"_{embed_suffix}"):
                    collection_input.set_value(f"{base}_{embed_suffix}")
            else:
                if base.endswith(f"_{embed_suffix}"):
                    collection_input.set_value(base[: -len(f"_{embed_suffix}")])

        ui.checkbox(
            f"Append embedding model to collection name  ({embed_suffix})",
            on_change=lambda e: _update_collection_name(e.value),
        )

        # ── Progress area (hidden until run) ──────────────────────
        progress_area = ui.column().classes("w-full gap-2")

        # ── Run ────────────────────────────────────────────────────
        async def run_ingest() -> None:
            source = source_input.value.strip()
            if not source:
                ui.notify("Please enter a source directory.", type="warning")
                return

            collection = collection_input.value.strip() or state.collection_name
            db_path = db_path_input.value.strip() or state.db_path
            embedding_model = state.config.get("embedding_model") or ""

            # ── Pre-flight: detect model mismatch before starting ──
            try:
                from synapse_core import collection_stats, list_collections
                existing = list_collections(db_path)
                if collection in existing:
                    stats = collection_stats(db_path, collection)
                    stored_model = stats.embedding_model or ""
                    chosen_model = embedding_model or "all-MiniLM-L6-v2"
                    if stored_model and stored_model != chosen_model:
                        with ui.dialog() as dlg, ui.card().classes("q-pa-md gap-3"):
                            ui.label("Embedding model mismatch").classes("text-subtitle1 text-warning")
                            ui.label(
                                f'Collection "{collection}" was built with '
                                f'"{stored_model}" but you are now using "{chosen_model}". '
                                "Mixing models in the same collection will corrupt search results."
                            ).classes("text-body2")
                            ui.label(
                                "Rename the collection, purge it first, or switch back to the original model."
                            ).classes("text-caption text-grey-5")
                            with ui.row().classes("justify-end q-mt-sm"):
                                ui.button("Cancel", on_click=lambda: dlg.submit(False)).props("flat dense color=primary")
                        await dlg
                        return
            except Exception:
                pass  # if the check fails, let ingest proceed and surface its own error

            progress_area.clear()
            with progress_area:
                prog_bar = ui.linear_progress(value=0).classes("w-full")
                prog_label = ui.label("Preparing…").classes("text-caption text-grey-5")

            # Yield to the event loop so NiceGUI pushes the progress UI to the client
            # before the worker thread starts (otherwise the bar never appears).
            await asyncio.sleep(0)

            # Shared dict updated by on_progress callback (called from worker thread)
            _prog: dict = {"done": 0, "total": 0, "filename": "", "status": ""}

            def on_progress(p) -> None:
                _prog["done"] = p.files_done
                _prog["total"] = p.files_total
                _prog["filename"] = p.filename
                _prog["status"] = p.status

            def update_ui() -> None:
                total = max(_prog["total"], 1)
                ratio = _prog["done"] / total
                prog_bar.set_value(ratio)
                pct = int(ratio * 100)
                prog_label.set_text(
                    f"{pct}%  —  {_prog['status']}: {_prog['filename']}  ({_prog['done']}/{_prog['total']})"
                )

            timer = ui.timer(0.15, update_ui)

            try:
                from synapse_core import ingest
                extra = {"embedding_model": embedding_model} if embedding_model else {}
                result = await asyncio.to_thread(
                    ingest,
                    source_dir=source,
                    db_path=db_path,
                    collection_name=collection,
                    on_progress=on_progress,
                    **extra,
                )
            except Exception as exc:
                timer.cancel()
                progress_area.clear()
                with progress_area:
                    ui.label(f"Ingest failed: {exc}").classes("text-negative text-caption")
                ui.notify(f"Ingest failed: {exc}", type="negative")
                return

            timer.cancel()
            progress_area.clear()
            with progress_area:
                prog_bar2 = ui.linear_progress(value=1).classes("w-full")
                prog_bar2.props("color=positive")

                with ui.card().classes("w-full q-mt-sm"):
                    ui.label("Ingest complete").classes("text-subtitle2 text-positive")
                    ui.separator()
                    with ui.grid(columns=2).classes("gap-x-8 gap-y-1 text-caption"):
                        ui.label("Sources found")
                        ui.label(str(result.sources_found))
                        ui.label("Sources ingested")
                        ui.label(str(result.sources_ingested))
                        ui.label("Sources skipped")
                        ui.label(str(result.sources_skipped))
                        ui.label("Chunks stored")
                        ui.label(str(result.chunks_stored))

        # Button defined after run_ingest so the closure can reference start_btn
        start_btn = ui.button("Start Ingest", icon="upload").props("color=primary")

        async def _guarded() -> None:
            start_btn.props("loading disable")
            try:
                await run_ingest()
            finally:
                start_btn.props(remove="loading disable")

        start_btn.on("click", _guarded)
