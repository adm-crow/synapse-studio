import asyncio
from nicegui import ui
from synapse_studio.layout import build_layout
from synapse_studio.state import state, ChatMessage


def _load_collections() -> list[str]:
    try:
        from synapse_core import list_collections
        return list_collections(state.db_path)
    except Exception:
        return []


@ui.page("/chat")
def chat_page() -> None:
    build_layout("/chat")

    ui.add_head_html("<style>.q-message-name { color: white !important; }</style>")

    with ui.column().classes("w-full q-pa-md gap-4"):
        ui.label("Chat").classes("text-h5")

        # ── Config bar ─────────────────────────────────────────────
        collections = _load_collections()
        with ui.row().classes("w-full gap-4 items-end"):
            collection_select = ui.select(
                options=collections,
                value=collections[0] if collections else None,
                label="Collection",
            ).classes("flex-1")
            n_ctx = ui.number("Context chunks", value=5, min=1, max=20).classes("w-36")
            ui.button(
                icon="refresh",
                on_click=lambda: ui.navigate.to("/chat"),
            ).props("flat color=grey-5 dense").tooltip("Refresh collections")

        # ── Chat history ───────────────────────────────────────────
        chat_area = ui.scroll_area().classes("w-full border rounded-lg bg-grey-9").style("height: 420px")
        messages_col: ui.column | None = None

        def render_history() -> None:
            nonlocal messages_col
            chat_area.clear()
            messages_col = None
            with chat_area:
                with ui.column().classes("w-full q-pa-md gap-2") as col:
                    messages_col = col
                    if not state.chat_history:
                        ui.label("Ask a question about your documents…").classes(
                            "text-grey-5 text-center q-mt-xl"
                        )
                        return
                    for msg in state.chat_history:
                        with ui.chat_message(name=msg.name, sent=msg.sent).classes("w-full"):
                            if msg.sent:
                                ui.label(msg.text)
                            else:
                                ui.markdown(msg.text)

        render_history()

        # ── Input area ─────────────────────────────────────────────
        with ui.row().classes("w-full items-end gap-2"):
            question_input = ui.input(placeholder="Ask a question…").classes("flex-1").props(
                "outlined dense"
            )

            async def send() -> None:
                text = question_input.value.strip()
                if not text:
                    return
                if not state.provider:
                    ui.notify("Configure an AI provider in Settings first.", type="warning")
                    return

                question_input.set_value("")
                question_input.props("disable")

                # 1 — show user message immediately
                state.chat_history.append(ChatMessage(text=text, sent=True, name="You"))
                render_history()

                # 2 — append thinking dots to the messages column
                if messages_col is None:
                    return
                with messages_col:
                    thinking = ui.row().classes("items-center gap-2 q-py-xs q-px-sm")
                    with thinking:
                        ui.element("q-spinner-dots").props("color=primary size=1.5em")

                await asyncio.sleep(0)  # flush UI so dots appear before blocking calls

                # 3 — retrieve context + generate answer (off the event loop)
                try:
                    from synapse_core import query, generate_answer, collection_stats
                    col_name = collection_select.value or state.collection_name
                    try:
                        stats = await asyncio.to_thread(collection_stats, state.db_path, col_name)
                        col_model = stats.embedding_model or None
                    except Exception:
                        col_model = None
                    results = await asyncio.to_thread(
                        query,
                        text=text,
                        db_path=state.db_path,
                        collection_name=col_name,
                        n_results=int(n_ctx.value),
                        embedding_model=col_model,
                    )
                    context = "\n\n".join(r["text"] for r in results)
                    answer = await asyncio.to_thread(
                        generate_answer,
                        question=text,
                        context=context,
                        provider=state.provider,
                        model=state.model,
                    )
                except Exception as exc:
                    answer = f"Error: {exc}"

                # 4 — replace dots with AI answer
                state.chat_history.append(
                    ChatMessage(text=answer, sent=False, name="Synapse")
                )
                render_history()
                question_input.props(remove="disable")

            question_input.on("keydown.enter", send)
            ui.button(icon="send", on_click=send).props("color=primary round dense")

        # ── Clear history ──────────────────────────────────────────
        def clear_history() -> None:
            state.chat_history.clear()
            render_history()

        ui.button("Clear history", icon="delete_outline", on_click=clear_history).props(
            "flat color=grey-5 dense"
        ).classes("self-start")
