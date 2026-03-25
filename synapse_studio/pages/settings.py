from nicegui import ui
from synapse_core import DEFAULT_MODELS, PROVIDERS, detect_provider

from synapse_studio.layout import build_layout
from synapse_studio.state import state

# Each preset defines a light-mode and dark-mode primary color.
# Dark variants are lighter/more vibrant so they read well on dark backgrounds.
PRESETS: dict[str, tuple[str, str]] = {
    "Synapse": ("#6c5ce7", "#a29bfe"),
    "Ocean": ("#0984e3", "#74b9ff"),
    "Forest": ("#00b894", "#55efc4"),
    "Sunset": ("#e17055", "#fab1a0"),
    "Rose": ("#e84393", "#fd79a8"),
}


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Expected 6-character hex, got: {h!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(hex1: str, hex2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"


@ui.page("/settings")
def settings_page() -> None:
    build_layout("/settings")

    with ui.column().classes("w-full q-pa-md gap-4"):
        ui.label("Settings").classes("text-h5")

        with ui.row().classes("w-full gap-6 items-start"):

            # ── Left column: Database + AI Provider ────────────────
            with ui.column().classes("flex-1 gap-6"):

                with ui.card().classes("w-full"):
                    ui.label("Database").classes("text-subtitle1 q-mb-sm")
                    db_path_input = ui.input(
                        label="DB path",
                        value=state.config.get("db_path", state.db_path),
                    ).classes("w-full")
                    collection_input = ui.input(
                        label="Default collection",
                        value=state.config.get(
                            "collection_name", state.collection_name
                        ),
                    ).classes("w-full")
                    embedding_model_input = ui.input(
                        label="Embedding model",
                        value=state.config.get("embedding_model", ""),
                        placeholder="all-MiniLM-L6-v2",
                    ).classes("w-full")
                    with ui.column().classes("gap-1 q-mt-xs"):
                        with ui.row().classes("items-start gap-1"):
                            ui.icon("info_outline").classes("text-info").style(
                                "font-size:14px; margin-top:2px; flex-shrink:0"
                            )
                            ui.html(
                                "Any <code>sentence-transformers</code> model name works"
                                " (e.g. <code>all-mpnet-base-v2</code>, <code>BAAI/bge-base-en-v1.5</code>).</br>Browse:"
                                " <a href='https://huggingface.co/models?library=sentence-transformers&sort=downloads'"
                                "    target='_blank' style='color:inherit'>Hugging Face</a>"
                                " &middot;"
                                " <a href='https://huggingface.co/spaces/mteb/leaderboard'"
                                "    target='_blank' style='color:inherit'>MTEB Leaderboard</a>"
                                " &middot;"
                                " <a href='https://www.sbert.net/docs/sentence_transformer/pretrained_models.html'"
                                "    target='_blank' style='color:inherit'>sbert.net</a>."
                            ).classes("text-caption text-info")
                        with ui.row().classes("items-start gap-1"):
                            ui.icon("warning_amber").classes("text-warning").style(
                                "font-size:14px; margin-top:2px; flex-shrink:0"
                            )
                            ui.label(
                                "Changing the embedding model requires re-running Ingest."
                            ).classes("text-caption text-warning")

                detected = detect_provider()
                with ui.card().classes("w-full"):
                    ui.label("AI Provider").classes("text-subtitle1 q-mb-sm")

                    if detected:
                        ui.label(f"Auto-detected: {detected}").classes(
                            "text-caption text-positive q-mb-sm"
                        )

                    provider_select = ui.select(
                        options=list(PROVIDERS),
                        value=state.config.get("provider") or detected or PROVIDERS[0],
                        label="Provider",
                    ).classes("w-full")

                    model_input = ui.input(
                        label="Model",
                        value=state.config.get(
                            "model",
                            DEFAULT_MODELS.get(
                                state.config.get("provider", detected or ""), ""
                            ),
                        ),
                    ).classes("w-full")

                    def on_provider_change(e) -> None:
                        model_input.set_value(DEFAULT_MODELS.get(e.value, ""))

                    provider_select.on("update:model-value", on_provider_change)

                    api_key_input = ui.input(
                        label="API key",
                        value=state.config.get("api_key", ""),
                        password=True,
                        password_toggle_button=True,
                    ).classes("w-full")

            # ── Right column: Theme ────────────────────────────────
            with ui.column().classes("flex-1 gap-6"):

                with ui.card().classes("w-full"):
                    ui.label("Theme").classes("text-subtitle1 q-mb-sm")

                    cur_light = state.config.get("theme_primary", "#6c5ce7")
                    cur_dark = state.config.get("theme_primary_dark", "#a29bfe")

                    # Light mode color
                    with ui.row().classes("w-full items-center gap-3"):
                        color_light = ui.color_input(
                            label="Light mode color", value=cur_light
                        ).classes("flex-1")
                        preview_light = ui.element("div").style(
                            f"width:36px;height:36px;border-radius:8px;flex-shrink:0;"
                            f"background:{cur_light};border:1px solid rgba(0,0,0,0.15)"
                        )

                    # Dark mode color
                    with ui.row().classes("w-full items-center gap-3"):
                        color_dark = ui.color_input(
                            label="Dark mode color", value=cur_dark
                        ).classes("flex-1")
                        preview_dark = ui.element("div").style(
                            f"width:36px;height:36px;border-radius:8px;flex-shrink:0;"
                            f"background:{cur_dark};border:1px solid rgba(255,255,255,0.15)"
                        )

                    # Live palette preview
                    with ui.row().classes("gap-3 q-mt-sm items-end"):
                        palette_swatches: list = []
                        for label_txt, color, border in [
                            ("Light", cur_light, "rgba(0,0,0,0.15)"),
                            (
                                "L+tint",
                                _mix(cur_light, "#ffffff", 0.4),
                                "rgba(0,0,0,0.1)",
                            ),
                            ("Dark", cur_dark, "rgba(255,255,255,0.15)"),
                            (
                                "D+tint",
                                _mix(cur_dark, "#ffffff", 0.4),
                                "rgba(255,255,255,0.1)",
                            ),
                            ("Positive", "#00b894", "rgba(0,0,0,0.1)"),
                            ("Negative", "#d63031", "rgba(0,0,0,0.1)"),
                            ("Warning", "#fdcb6e", "rgba(0,0,0,0.1)"),
                        ]:
                            with ui.column().classes("items-center gap-1"):
                                sw = ui.element("div").style(
                                    f"width:26px;height:26px;border-radius:6px;"
                                    f"background:{color};border:1px solid {border}"
                                )
                                ui.label(label_txt).classes(
                                    "text-caption text-grey-5"
                                ).style("font-size:9px")
                                palette_swatches.append(sw)

                    def _refresh(light: str, dark: str) -> None:
                        try:
                            _hex_to_rgb(light)
                            _hex_to_rgb(dark)
                        except (ValueError, IndexError):
                            return  # invalid hex — skip update
                        preview_light.style(
                            f"width:36px;height:36px;border-radius:8px;flex-shrink:0;"
                            f"background:{light};border:1px solid rgba(0,0,0,0.15)"
                        )
                        preview_dark.style(
                            f"width:36px;height:36px;border-radius:8px;flex-shrink:0;"
                            f"background:{dark};border:1px solid rgba(255,255,255,0.15)"
                        )
                        new_colors = [
                            light,
                            _mix(light, "#ffffff", 0.4),
                            dark,
                            _mix(dark, "#ffffff", 0.4),
                        ]
                        for i, c in enumerate(new_colors):
                            palette_swatches[i].style(
                                f"width:26px;height:26px;border-radius:6px;background:{c};"
                                f"border:1px solid rgba(128,128,128,0.2)"
                            )

                    color_light.on_value_change(
                        lambda e: _refresh(e.value, color_dark.value)
                    )
                    color_dark.on_value_change(
                        lambda e: _refresh(color_light.value, e.value)
                    )

                    # Presets
                    ui.label("Presets").classes("text-caption text-grey-5 q-mt-sm")
                    with ui.row().classes("gap-2 flex-wrap q-mt-xs"):
                        for name, (hl, hd) in PRESETS.items():

                            def _pick(e, light=hl, dark=hd) -> None:
                                color_light.set_value(light)
                                color_dark.set_value(dark)
                                _refresh(light, dark)

                            ui.button(name, on_click=_pick).style(
                                f"background:linear-gradient(135deg,{hl} 50%,{hd} 50%);"
                                f"color:white;min-width:80px"
                            ).props("dense no-caps rounded")

                    ui.separator().classes("q-my-sm")

                    # Dark mode toggle — applied on Save, not immediately
                    dark_switch = ui.switch(
                        "Dark mode", value=state.config.get("dark_mode", False)
                    )

                    ui.separator().classes("q-my-sm")

                    def save_and_reload() -> None:
                        _persist()
                        ui.navigate.to("/settings")

                    ui.button(
                        "Save & Reload theme", icon="palette", on_click=save_and_reload
                    ).props("color=primary")

        # ── Save ───────────────────────────────────────────────────
        def _persist() -> None:
            new_values = {
                "db_path": db_path_input.value.strip(),
                "collection_name": collection_input.value.strip(),
                "embedding_model": embedding_model_input.value.strip(),
                "provider": provider_select.value,
                "model": model_input.value.strip(),
                "api_key": api_key_input.value,
                "theme_primary": color_light.value,
                "theme_primary_dark": color_dark.value,
                "dark_mode": dark_switch.value,
            }
            old_values = {k: state.config.get(k) for k in new_values}
            state.config.update(new_values)
            try:
                state.save()
                ui.notify("Settings saved.", type="positive")
            except Exception as exc:
                state.config.update(old_values)  # revert in-memory state on failure
                ui.notify(f"Failed to save: {exc}", type="negative")

        ui.button("Save", icon="save", on_click=_persist).props("color=primary")
