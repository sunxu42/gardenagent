"""Bootstrap the agent workspace directory.

Historically this also seeded the workspace with bootstrap-style markdown
files (AGENTS.md / SOUL.md / IDENTITY.md / BOOTSTRAP.md / USER.md /
HEARTBEAT.md). The system prompt is now composed deterministically from
`prompts/*.yaml` via `agent.middlewares.SystemPromptMiddleware`, so we no longer copy
those template files into the workspace. We still seed the `skills/`
folder because `SkillsMiddleware` reads it from the backend root.
"""

import os
import shutil

from shared.config.paths import DEFAULT_PROMPTS_DIR, resolve_reference_dir


def init_workspace(workspace_dir: str) -> str:
    if os.path.exists(workspace_dir):
        return workspace_dir

    os.makedirs(workspace_dir)

    skills_dst = os.path.join(workspace_dir, "skills")
    skills_src = resolve_reference_dir() / "skills"
    if skills_src.is_dir() and not os.path.exists(skills_dst):
        shutil.copytree(skills_src, skills_dst)

    return workspace_dir
