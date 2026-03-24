from __future__ import annotations

from pathlib import Path
from typing import Annotated

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.types import Command

from deepagents.backends.utils import validate_path
from deepagents.middleware.filesystem import FilesystemMiddleware, FilesystemState

DELETE_FILE_TOOL_DESCRIPTION = """Deletes a file from the filesystem.

Usage:
- Use this tool only when the user explicitly asks to delete a file.
- The file path must be absolute.
- This tool deletes files only (not directories).
- Prefer read_file/ls first when uncertain about the target path.
"""


class FilesystemPlusMiddleware(FilesystemMiddleware):
    """Filesystem middleware with an extra delete_file tool."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools.append(self._create_delete_file_tool())

    def _create_delete_file_tool(self) -> BaseTool:
        tool_description = self._custom_tool_descriptions.get("delete_file") or DELETE_FILE_TOOL_DESCRIPTION

        def sync_delete_file(
            file_path: Annotated[str, "Absolute path to the file to delete. Must be absolute, not relative."],
            runtime: ToolRuntime[None, FilesystemState],
        ) -> Command | str:
            resolved_backend = self._get_backend(runtime)
            try:
                validated_path = validate_path(file_path)
            except ValueError as e:
                return f"Error: {e}"

            # Filesystem-like backends expose _resolve_path and operate on real files.
            if hasattr(resolved_backend, "_resolve_path"):
                try:
                    resolved_path = resolved_backend._resolve_path(validated_path)  # ty: ignore[attr-defined]
                    p = Path(resolved_path)
                    if not p.exists():
                        return f"Error: File '{validated_path}' not found"
                    if p.is_dir():
                        return f"Error: '{validated_path}' is a directory. delete_file only supports files."
                    p.unlink()
                    return f"Deleted file {validated_path}"
                except ValueError as e:
                    return f"Error: {e}"
                except OSError as e:
                    return f"Error deleting file '{validated_path}': {e}"

            # State-like backends can delete by returning files_update marker.
            state_files = runtime.state.get("files", {})
            if validated_path not in state_files:
                return f"Error: File '{validated_path}' not found"
            return Command(
                update={
                    "files": {validated_path: None},
                    "messages": [
                        ToolMessage(
                            content=f"Deleted file {validated_path}",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                }
            )

        async def async_delete_file(
            file_path: Annotated[str, "Absolute path to the file to delete. Must be absolute, not relative."],
            runtime: ToolRuntime[None, FilesystemState],
        ) -> Command | str:
            return sync_delete_file(file_path, runtime)

        return StructuredTool.from_function(
            name="delete_file",
            description=tool_description,
            func=sync_delete_file,
            coroutine=async_delete_file,
        )
