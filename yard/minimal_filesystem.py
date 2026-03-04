"""
Minimal FilesystemMiddleware: 只暴露部分文件工具，避免 7 个工具全开。

会同步保留并注入与「实际暴露工具」一致的 system prompt，不会提到未暴露的工具。

用法:
    from yard.minimal_filesystem import MinimalFilesystemMiddleware
    from deepagents.backends import FilesystemBackend

    backend = FilesystemBackend(root_dir=WORK_DIR)
    fs = MinimalFilesystemMiddleware(
        backend=backend,
        tools_include=["ls", "read_file", "write_file"],
    )
    create_deep_agent(..., middleware=[fs])
"""
from deepagents.middleware.filesystem import FilesystemMiddleware

# 默认只保留最常用的 3 个，技能按 path 读 SKILL.md 够用
DEFAULT_TOOLS = ("ls", "read_file", "write_file")

ALL_TOOL_NAMES = ("ls", "read_file", "write_file", "edit_file", "glob", "grep", "execute")

# 简短说明，只给实际暴露的工具用
_TOOL_PROMPT_LINES = {
    "ls": "ls: list files in a directory (requires absolute path)",
    "read_file": "read_file: read a file from the filesystem",
    "write_file": "write_file: write to a file in the filesystem",
    "edit_file": "edit_file: edit a file in the filesystem",
    "glob": "glob: find files matching a pattern (e.g., **/*.py)",
    "grep": "grep: search for text within files",
    "execute": "execute: run a shell command in the sandbox (returns output and exit code)",
}


def _build_minimal_system_prompt(tool_names: list[str]) -> str:
    """只描述当前暴露的文件/执行工具，避免 prompt 里出现不存在的工具。"""
    parts = [
        "## Filesystem Tools " + ", ".join(f"`{n}`" for n in tool_names),
        "You have access to a filesystem which you can interact with using these tools.",
        "All file paths must start with /.",
        "",
    ]
    for n in tool_names:
        if n in _TOOL_PROMPT_LINES:
            parts.append("- " + _TOOL_PROMPT_LINES[n])
    return "\n".join(parts)


class MinimalFilesystemMiddleware(FilesystemMiddleware):
    """只注册指定文件工具，并注入与之一致的 system prompt。"""

    def __init__(
        self,
        *,
        tools_include: tuple[str, ...] | list[str] | None = None,
        tools_exclude: tuple[str, ...] | list[str] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        name_of = lambda t: getattr(t, "name", None)
        if tools_include is not None:
            include_set = set(tools_include)
            self.tools = [t for t in self.tools if name_of(t) in include_set]
        elif tools_exclude is not None:
            exclude_set = set(tools_exclude)
            self.tools = [t for t in self.tools if name_of(t) not in exclude_set]
        else:
            self.tools = [t for t in self.tools if name_of(t) in set(DEFAULT_TOOLS)]
        # 只对当前暴露的工具保留 prompt，避免模型以为有 edit_file/glob/grep/execute
        names = [name_of(t) for t in self.tools if name_of(t)]
        self._custom_system_prompt = _build_minimal_system_prompt(names)
