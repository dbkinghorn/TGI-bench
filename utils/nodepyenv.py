#!/usr/bin/env python
"""
nodepyenv.py creates an isolated no-dependency conda virtual environment using micromamba

It is a small package using only standard python libraries. It would be easy to use with PyInstaller to create a standalone executable with zero dependencies.

nodepyenv.py can be "compiled" to a standalone executable using PyInstaller with the command:
pyinstaller --onefile nodepyenv.py

It can be run directly with python:
python nodepyenv.py

Or it can be imported as a module:
from nodepyenv import create_env

micromamba is small self-contained conda package manager written in C++
https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html

Linux, Windows, and MacOS(arm64) are supported (Only Linux and Windows in this version.)
MacOS support should be simple to add since there are precompiled micromamba binaries for MacOS(arm64) and MacOS(intel) available.

The environment files are created in the same directory (mamba_root) as the environment.yaml file within subdirectories ./env ./pkgs.

The optional arguments are the path to the mamba_root directory (deafult is current directory) and the name of environment YAML file (default environment.yaml). If no arguments are given, the defaults are used.

The program,
- Checks to see if micromamba is present in the mamba_root directory
- If needed, downloads the latest micromamba from the micromamba github release page
- Creates a conda environment in the mamba_root directory by installing the packages specified in the environment.yaml file
- Prints the path to the python executable in the environment

The returned python executable can be used to run commands directly in the environment. 

For example, to run the python interpreter in the environment, use the command:
./envs/<env_name>/bin/python <your python application>
or use micromamba and the python executable in the environment with:
./micromamba -r . run -n <env_name> python <your python application>


"""

import argparse
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import sys
import urllib.request

VERSION = "0.1.0"
MICROMAMBA_BASE_URL = (
    "https://github.com/mamba-org/micromamba-releases/releases/latest/download"
)
system = platform.system()


# Utility function to extract a value from a yaml file using a regular expression
# Returns the match for value on key: value or None. Does not require external packages!
def get_value_from_yaml(file_path, key):
    with open(file_path, "r") as f:
        for line in f:
            match = re.search(rf"^{key}:\s*(.+)$", line)
            if match:
                return match.group(1)
    return None


# Download micromamba
def download_micromamba(mamba_root: Path, system: str):
    if system == "Windows":
        url = f"{MICROMAMBA_BASE_URL}/micromamba-win-64"
        download_path = mamba_root / "micromamba.exe"
    elif system == "Linux":
        url = f"{MICROMAMBA_BASE_URL}/micromamba-linux-64"
        download_path = mamba_root / "micromamba"
    elif system == "Darwin":
        url = f"{MICROMAMBA_BASE_URL}/micromamba-osx-arm64"
        download_path = mamba_root / "micromamba.x"
    else:
        print("Unsupported platform")
        sys.exit(1)

    try:
        print(f"Downloading micromamba from {url}")
        micromamba_path, HTTPMessage = urllib.request.urlretrieve(url, download_path)
        # Make micromamba executable
        download_path.chmod(0o755)

        print(f"micromamba_path: {micromamba_path}")
        print(f"download_path: {download_path}")
    except:
        print("Error downloading micromamba")
        print(HTTPMessage)
        sys.exit(1)
    return micromamba_path


# Check if micromamba is present in the mamba_root.
# If not, download it.
def check_micromamba(mamba_root: Path, system: str):
    if system == "Windows":
        micromamba = mamba_root / "micromamba.exe"
    elif system == "Linux":
        micromamba = mamba_root / "micromamba"
    elif system == "Darwin":
        micromamba = mamba_root / "micromamba.x"
    else:
        print("Unsupported platform")
        sys.exit(1)
    if not micromamba.exists():
        print("\nmicromamba not found, downloading micromamba")
        # Download micromamba from the micromamba github release page
        micromamba_path = download_micromamba(mamba_root, system)
        print(f"micromamba downloaded to {micromamba_path}")
    else:
        micromamba_path = micromamba
        print(f"micromamba found at {micromamba_path}")
    return micromamba_path


# Create a conda environment from the environment.yaml file
def create_env(mamba_root, file_name="environment.yaml"):
    micromamba_path = check_micromamba(mamba_root, system)
    # Check if environment.yaml is present in the mamba_root directory
    env_file = mamba_root / f"""{file_name}"""
    if not env_file.exists():
        print(f"{env_file} not found. Please create an environment.yaml file")
        sys.exit(1)
    # Check if environment.yaml has a name
    env_name = get_value_from_yaml(env_file, "name")
    if env_name is None:
        print(
            f"{env_file} does not have a name: value entry.\nPlease add a name: value entry to the environment.yaml file\n run with --help for more information."
        )
        sys.exit(1)

    print(f"\nCreating conda environment {env_name} from {env_file}")
    cmd = f"{micromamba_path} env create --yes -r {mamba_root} -f {env_file} "
    process = subprocess.Popen(
        shlex.split(cmd, posix=(os.name == "posix")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
    returncode = process.poll()

    # Check if the conda environment was created successfully
    if returncode != 0:
        print("Error creating conda environment")
        sys.exit(1)
    else:
        print(f"\nConda environment {env_name} created successfully")
        if platform.system() == "Windows":
            python_path = mamba_root / "envs" / env_name / "python.exe"
        else:
            python_path = mamba_root / "envs" / env_name / "bin" / "python"  # Linux

        # run commands directly with ./micromamba -r . run -n {env_name} <command> \nor
        print(f"Use the python executable in the environment with {python_path}")
        return python_path


# Main program
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Create a conda environment in the current mamba_root directory from an environment.yaml file. See https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually for YAML file format."""
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{Path(__file__).name} version {VERSION}",
    )
    parser.add_argument(
        "-f",
        "--envfile",
        action="store",
        dest="envfile",
        default="environment.yaml",
        help="environment.yaml file to use",
    )
    parser.add_argument(
        "-r",
        "--mamba_root",
        action="store",
        dest="mamba_root",
        default=Path().cwd(),
        help="mamba root directory",
    )

    args = parser.parse_args()
    mamba_root = Path(args.mamba_root).absolute()
    envfile = args.envfile

    create_env(mamba_root, envfile)
