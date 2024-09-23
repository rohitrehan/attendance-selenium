import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def run_shell(s: str, **kwargs) -> None:
    print(">", s)
    subprocess.check_call(s, shell=True, **kwargs)


@dataclass
class Args:
    force: bool


ROOT_DIR = Path(__file__).absolute().parent
SRC_DIR = ROOT_DIR


def write_docker_build_file_for_compiling(target: Path, version: str = "3.10") -> None:
    content = f"""FROM public.ecr.aws/lambda/python:{version} AS build-stage

WORKDIR /deps
COPY ./requirements.in .
RUN pip install pip-tools
RUN pip-compile --output-file requirements.txt requirements.in
RUN ls

FROM scratch as export-stage
COPY --from=build-stage /deps/requirements.txt .
    """
    with Path.open(target / "Dockerfile_pipcompile", "w") as f:
        f.write(content)


def has_file_changed(file_path: Path):
    """
    Check if the given file has been changed in the Git repository.
    """
    try:
        # Check if the file is in the Git repository
        subprocess.check_output(
            ["git", "ls-files", "--error-unmatch", file_path.resolve()]
        )
        # Check if the file has been modified
        result = subprocess.run(
            ["git", "diff", "--name-only", "--exit-code", file_path],
            capture_output=True,
        )
        return result.returncode != 0
    except subprocess.CalledProcessError:
        # File not found in the repository
        return False


def compile_requirements(dir: Path, version="3.10", force=False):
    if not force and not has_file_changed(dir / "requirements.in"):
        print(f'{(dir / "requirements.in").resolve()} has not changed')
        return 0

    try:
        try:
            Path(dir / "requirements.txt").unlink()
        except Exception:
            pass  # ignore if file does not exist

        env = os.environ.copy()
        env["DOCKER_BUILDKIT"] = "1"
        write_docker_build_file_for_compiling(dir, version)
        run_shell(
            "docker build --file Dockerfile_pipcompile --output . . --network host --no-cache",
            env=env,
            cwd=dir,
        )
        Path(dir / "Dockerfile_pipcompile").unlink()
    except Exception as e:
        try:
            Path(dir / "Dockerfile_pipcompile").unlink()
        except Exception:
            pass  # ignore if file does not exist
        print(f"Error compiling requirements for {dir}", e)
        return 1

    return 0


def main(args: Args) -> int:
    compile_requirements(SRC_DIR, "3.10", args.force)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", action="store_true")
    args = Args(**vars(parser.parse_args()))
    print(args.__dict__)
    main(args)
