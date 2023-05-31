#!/usr/bin/env python3
import sys
import os
import shutil
import json
import subprocess


def test(id):
    shutil.rmtree(f"build/test/{id}", ignore_errors=True)
    os.makedirs(f"build/test/{id}", exist_ok=True)
    shutil.copytree(f"src/{id}/.devcontainer", f"build/test/{id}/.devcontainer")
    shutil.copyfile(f"test/{id}/test.sh", f"build/test/{id}/test.sh")

    with open(f"src/{id}/devcontainer-template.json") as f:
        options = json.load(f)["options"]
    find_replace = {}
    for option in options:
        option_find = f"${{templateOption:{option}}}"
        option_replace = options[option]["default"]
        if not option_replace:
            raise Exception(f"Option {option} has no default value")
        find_replace[option_find] = option_replace

    for root, dirs, files in os.walk(f"build/test/{id}/.devcontainer"):
        for file in files:
            with open(f"{root}/{file}", "r+") as f:
                content = f.read()
                for find, replace in find_replace.items():
                    content = content.replace(find, replace)
                f.seek(0)
                f.write(content)
                f.truncate()

    label = f"test-container={id}"
    subprocess.run(
        f"devcontainer up --id-label {label} --workspace-folder build/test/{id}".split(),
        check=True,
    )
    subprocess.run(
        f"devcontainer exec --id-label {label} --workspace-folder build/test/{id} /bin/bash -ec ./test.sh".split(),
        check=True,
    )
    x = (
        subprocess.run(
            f"docker container ls -f label={label} -q".split(),
            capture_output=True,
            check=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    subprocess.run(f"docker rm -f {x}".split(), check=True)


def find_all_ids():
    ids = []
    for root, dirs, files in os.walk("src"):
        if "devcontainer-template.json" in files:
            ids.append(os.path.basename(root))
    return ids


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        ids = find_all_ids()
    else:
        ids = args

    for id in ids:
        print(f"Testing {id}...")
        test(id)


if __name__ == "__main__":
    main()
