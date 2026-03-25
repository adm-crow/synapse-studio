import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_TOML = "synapse.toml"


@dataclass
class ChatMessage:
    text: str
    sent: bool  # True = user, False = assistant
    name: str = ""


@dataclass
class AppState:
    cwd: Path = field(default_factory=lambda: Path(os.getcwd()))
    config: dict = field(default_factory=dict)
    chat_history: list[ChatMessage] = field(default_factory=list)
    model_ready: bool = False

    def load(self) -> None:
        """Read synapse.toml and populate config with normalised keys."""
        # Sensible defaults before reading the file
        self.config = {
            "db_path":        str(self.cwd / "synapse_db"),
            "collection_name": "default",
            "embedding_model": "",
            "provider": "",
            "model":    "",
            "api_key":  "",
            "theme_primary":      "#6c5ce7",
            "theme_primary_dark": "#a29bfe",
            "dark_mode": False,
        }

        config_path = self.cwd / _TOML
        if not config_path.exists():
            self.apply_env()
            return

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            self.apply_env()
            return

        # [synapse] section — synapse-core uses "db" and "collection" as key names
        synapse = data.get("synapse", {})
        if synapse.get("db"):
            self.config["db_path"] = synapse["db"]
        if synapse.get("collection"):
            self.config["collection_name"] = synapse["collection"]
        if synapse.get("embedding_model"):
            self.config["embedding_model"] = synapse["embedding_model"]

        # [studio] section — synapse-studio-specific settings
        studio = data.get("studio", {})
        for key in ("provider", "model", "api_key", "theme_primary", "theme_primary_dark"):
            if studio.get(key):
                self.config[key] = studio[key]
        if "dark_mode" in studio:
            self.config["dark_mode"] = bool(studio["dark_mode"])

        self.apply_env()

    def save(self) -> None:
        """Persist config back to synapse.toml."""
        from synapse_core import save_config

        # save_config writes the [synapse] section using its own key names
        synapse_keys: dict = {}
        if self.config.get("db_path"):
            synapse_keys["db"] = self.config["db_path"].replace("\\", "/")
        if self.config.get("collection_name"):
            synapse_keys["collection"] = self.config["collection_name"]
        if self.config.get("embedding_model"):
            synapse_keys["embedding_model"] = self.config["embedding_model"]

        save_config(synapse_keys, self.cwd)

        # Append/replace the [studio] section manually
        self._write_studio_section()
        self.apply_env()

    def _write_studio_section(self) -> None:
        config_path = self.cwd / _TOML
        existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""

        # Strip any existing [studio] section
        filtered: list[str] = []
        in_studio = False
        for line in existing.splitlines():
            if line.strip() == "[studio]":
                in_studio = True
                continue
            if in_studio and line.strip().startswith("["):
                in_studio = False
            if not in_studio:
                filtered.append(line)

        studio_lines = ["[studio]"]
        for key in ("provider", "model", "api_key", "theme_primary", "theme_primary_dark"):
            val = self.config.get(key, "")
            if val:
                escaped = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
                studio_lines.append(f'{key} = "{escaped}"')
        studio_lines.append(f'dark_mode = {str(self.config.get("dark_mode", False)).lower()}')

        base = "\n".join(filtered).rstrip()
        new_content = (base + "\n\n" if base else "") + "\n".join(studio_lines) + "\n"
        config_path.write_text(new_content, encoding="utf-8")

    def apply_env(self) -> None:
        """Push the stored API key into os.environ so synapse-core can pick it up."""
        api_key = self.config.get("api_key", "")
        if not api_key:
            return
        env_map = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
        env_var = env_map.get(self.config.get("provider", "").lower())
        if env_var:
            os.environ[env_var] = api_key

    @property
    def db_path(self) -> str:
        return self.config.get("db_path", str(self.cwd / "synapse_db"))

    @property
    def collection_name(self) -> str:
        return self.config.get("collection_name", "default")

    @property
    def provider(self) -> str:
        return self.config.get("provider", "")

    @property
    def model(self) -> str:
        return self.config.get("model", "")


# Module-level singleton — safe for native=True (single user)
state = AppState()
state.load()
