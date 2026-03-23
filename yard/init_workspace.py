# copy file from reference folder to workspace folder
import os
import shutil


def init_workspace():
    workspace_dir = "yard/workspace"
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)

    # copy file from reference folder to workspace folder
    for file in os.listdir("yard/reference"):
        if file.endswith(".md"):
            shutil.copy(os.path.join("yard/reference", file), os.path.join(workspace_dir, file))
    return workspace_dir