
# Jupyter Data Science Notebooks (jupyter-datascience-notebooks)

Use Jupyter Data Science Notebooks with Python, R, Julia, and more.

## Options

| Options Id | Description | Type | Default Value |
|-----|-----|-----|-----|
| baseVariant | Base image. Check the documentation for details. | string | datascience-notebook |
| imageVariant | Image version (tag). | string | latest |

<!-- markdownlint-disable MD041 -->

## Configurations

### Choosing a base image

You can choose from many base images to tailor the container to your project's needs.
If you don't know what this means, that's OK! Just choose the `datascience-notebook` option.
It has many packages for data science from the Julia, Python, and R communities. 🚀

📚 You can learn more about what each of these base images is and what features each of them
in [the Jupyter Docker Stacks reference page](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html).

### Default command

The default command of the base image is set to start the Jupyter server.
If you do not use the Jupyter server, comment out `"overrideCommand": false` of the devcontainer.json.

## Credits

This template was originally created by [@nathancarter](https://github.com/nathancarter)
and other contributors in the [microsoft/vscode-dev-containers](https://github.com/microsoft/vscode-dev-containers) repository.
It has since been landed here. 🌠


---

_Note: This file was auto-generated from the [devcontainer-template.json](https://github.com/devcontainers-community/templates/blob/main/src/jupyter-datascience-notebooks/devcontainer-template.json).  Add additional notes to a `NOTES.md`._
