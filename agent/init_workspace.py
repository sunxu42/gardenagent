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

from shared.config.paths import resolve_reference_dir


def _seed_skills(workspace_dir: str) -> None:
    skills_dst = os.path.join(workspace_dir, "skills")
    skills_src = resolve_reference_dir() / "skills"
    if skills_src.is_dir() and not os.path.exists(skills_dst):
        shutil.copytree(skills_src, skills_dst)


def init_workspace(workspace_dir: str) -> str:
    os.makedirs(workspace_dir, exist_ok=True)
    _seed_skills(workspace_dir)
    return workspace_dir
