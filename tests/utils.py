import os
import shutil

PYTHON_VERSION = (
    "3.12.2"  # make sure to keep this updated to a supported version
)


def copy_dir_to_tmp_path(scenario_dir, tmp_path):
    # Copy the scenario directory to a temporary directory
    for item in os.listdir(scenario_dir):
        s = os.path.join(scenario_dir, item)
        d = os.path.join(tmp_path, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
