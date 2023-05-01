#!/usr/bin/env python3
"""
Runs tests for a template. If no $1 argument is provided, this script will test
all templates in the src/ folder.

1. If there are no arguments, get a list of all src/* templates. If there are
    arguments, use $1 as the list of templates to test.
2. For each template:
    a. Copy the template to a temporary directory.
    b. Replace all template options with their default values.
    c. If there is a test/ folder, copy it to the temporary directory as a new
        test-project/ folder.
    d. If there is a test/common/ folder, copy it to the temporary directory
        into that new test-project/ folder so that it is available to all tests.
        This is the place to put common test scripts which can then be imported
        by each test script.
    e. Run the template's test.sh script, if it exists.
    f. Delete the temporary directory.
3. If any tests fail, exit with a non-zero code.
"""

from subprocess import run
from shutil import rmtree, copytree
from tempfile import TemporaryDirectory
from json import loads
from os import walk

def sh(comd: str): str
    """
    Runs a shell command and returns the STDOUT output. STDERR is output to this
    process's STDERR. STDOUT is captured and returned as a string. If this
    command causes an error, that error is raised.
    """

    return run(
        comd,
        shell=True,
        check=True,
        capture_output=True,
        encoding="utf-8",
    ).stdout.strip()

def instantiate_template(config_path: str, target_path: str): None
    """
    Instantiates a template by replacing all template options with their
    default values. This will modify the template files in-place.
    """

    # 1. Read the template's devcontainer-template.json file. We only care about
    #    the "options" object. Don't worry if "options" is missing or empty, we
    #    will deal with that shortly.
    with open(config_path) as f:
        options = loads(f.read())["options"]

    # 2. If there are no options, we are done!
    if not options:
        return

    # 3. For each option, make it into a find-replace pair. The find is the
    #    string "${templateOption:optionName}". The replace is the option's
    #    default value. If there is no default value, raise an error.
    find_replace = {}
    for option in options:
        option_find = "${templateOption:" + option + "}"
        option_replace = options[option]["default"]
        if not option_replace:
            raise Exception(
                f"Template '{id}' is missing a default value for " +
                f"option '{option}'. Try to add a default value to " +
                "the template's devcontainer-template.json file."
            )
        find_replace[option_find] = option_replace

    # 4. For each file in the target directory, replace all find strings with
    #    their replace strings. We do this in-place, so we don't need to return
    #    anything.
    for root, dirs, files in os.walk(target_path):
        for file in files:
            with open(os.path.join(root, file), "r+") as f:
                contents = f.read()
                for find, replace in find_replace.items():
                    contents = contents.replace(find, replace)
                f.seek(0)
                f.write(contents)
                f.truncate()

def test_template(id: str):
    """
    Tests a specific template. Given an ID, this will copy the template to a
    temporary directory, run any tests, and then delete the temporary. This will
    involve running a Docker container.
    """

    # 1. Create a temporary directory to copy the template to. We will delete
    #    this directory when we are done.
    with TemporaryDirectory() as tmp:
        # 2. Copy the template to the temporary directory.
        copytree(f"src/{id}", tmp)
        print(f"🟩 Copied template src/{id}/ to {tmp}/")

        # 3. If there is a test/test-project folder, we want to use that as a
        #    project to instantiate the devcontainer-template.json file into.
        if os.path.isdir(f"test/{id}/test-project"):
            copytree(f"test/{id}/test-project", f"{tmp}/test-project")
            print(f"🟩 Copied test/{id}/test-project/ to {tmp}/test-project/")
        else:
            os.mkdir(f"{tmp}/test-project")
            print(f"🟨 Created empty {tmp}/test-project/")

        # 4. If there is a test/_common folder, we want to copy that into the
        #    test-project folder so that it is available to all tests.
        if os.path.isdir(f"test/{id}/_common"):
            copytree(f"test/{id}/_common", f"{tmp}/test-project")
            print(f"🟩 Copied test/{id}/_common/ to {tmp}/test-project")

        # 5. Instantiate the template's devcontainer-template.json file.
        instantiate_template(f"{tmp}/devcontainer-template.json", f"{tmp}/test-project")



    trap 'rm -rf "$tmp"' SIGINT SIGTERM ERR EXIT
    tmp=$(mktemp -d)
    rsync -a "src/$1/" "$tmp/"
    echo "🟩 Copied template '$1' to '$tmp'"
    (
        cd "$tmp"

        options_object=( $(jq -r '.options' devcontainer-template.json) )
        if [[ -z $options_object || $options_object == "null" ]]; then
            exit
        fi

        option_names=( $(jq -r '.options | keys[]' devcontainer-template.json) )
        if [[ -z ${options[0]} || ${options[0]} == "null" ]]; then
            exit
        fi

        echo "🟩 Found options: ${option_names[*]}"
        for option_name in "${option_names[@]}"; do
            option_key="\${templateOption:$option_name}"
            option_value=$(jq -r ".options | .$option | .default" devcontainer-template.json)

            if [[ -z $option_value || $option_value == "null" ]]; then
                echo "Template '$1' is missing a default value for option '$option'" >&2
                exit 1
            fi

            option_value_escaped=$(sed -e 's/[]\/$*.^[]/\\&/g' <<<"$option_value")
            find . -type f -print0 | xargs -0 sed -i "s/$option_key/$option_value_escaped/g"
        done
    )

    if command -v tree &> /dev/null; then
        echo "🟦 Template '$1' after options substitution:"
        tree "$tmp"
    fi

    if [[ ! -d test/$1 ]]; then
        echo "🟨 No tests for template '$1'" >&2
        return
    fi

    tmp_project="$tmp/test-project"
    mkdir -p "$tmp_project"
    rsync -a "test/$1" "$tmp_project/"
    echo "🟩 Copied tests for template '$1' to '$tmp_project'"
    rsync -a test/common/ "$tmp_project/"
    echo "🟩 Copied common tests to '$tmp_project'"

    export DOCKER_BUILDKIT=1
    id_label="test-container=$1"
    devcontainer up --id-label "$id_label" --workspace-folder "$tmp"
    echo "🟩 Started container for template '$1'"
    devcontainer exec --id-label "$id_label" --workspace-folder "$tmp" /bin/sh -c '
        set -e
        if [ -f "test-project/test.sh" ]; then
            cd test-project
            if [ "$(id -u)" = "0" ]; then
                chmod +x test.sh
            else
                sudo chmod +x test.sh
            fi
            ./test.sh
        else
            ls -a
        fi
    '
    echo "🟩 Ran tests for template '$1'"
    docker rm -f "$(docker container ls -f "label=$id_label" -q)"
)

if [[ -n $1 ]]; then
    echo "🟪 Testing template '$1'..."
    test_template "$1"
else
    echo '🟥 Missing template ID argument!' >&2
    exit 1
fi
