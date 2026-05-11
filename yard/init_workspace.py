"""Bootstrap the agent workspace directory.

Historically this also seeded the workspace with bootstrap-style markdown
files (AGENTS.md / SOUL.md / IDENTITY.md / BOOTSTRAP.md / USER.md /
HEARTBEAT.md). The system prompt is now composed deterministically from
`prompts/*.yaml` via `yard.persona.PromptBuilder`, so we no longer copy
those template files into the workspace. We still seed the `skills/`
folder because `SkillsMiddleware` reads it from the backend root.
"""

import os
import shutil

REFERENCE_DIR = os.path.join("yard", "reference")
REFERENCE_SKILLS_DIR = os.path.join(REFERENCE_DIR, "skills")


def init_workspace(workspace_dir: str) -> str:
    if os.path.exists(workspace_dir):
        return workspace_dir

    os.makedirs(workspace_dir)

    skills_dst = os.path.join(workspace_dir, "skills")
    if os.path.isdir(REFERENCE_SKILLS_DIR) and not os.path.exists(skills_dst):
        shutil.copytree(REFERENCE_SKILLS_DIR, skills_dst)

    return workspace_dir
