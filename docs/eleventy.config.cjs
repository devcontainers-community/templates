const { readdir, readFile } = require("node:fs/promises");
const { marked } = require("marked");

// https://github.com/11ty/eleventy/issues/836
module.exports = exports = (ctx) => {
  const options = {
    dir: {
      input: "src",
      output: "dist",
    },
  };
  // https://www.11ty.dev/docs/config/#deploy-to-a-subdirectory-with-a-path-prefix
  if (process.env.BASE_URL) {
    options.pathPrefix = process.env.BASE_URL;
  }

  // https://www.11ty.dev/docs/copy/#emulate-passthrough-copy-during-serve
  ctx.setServerPassthroughCopyBehavior("passthrough");
  ctx.addPassthroughCopy("src/style.css");

  // https://www.11ty.dev/docs/data-global-custom/
  ctx.addGlobalData("templates", async () => {
    const templates = [];
    for (const name of await readdir("../src")) {
      const template = JSON.parse(
        await readFile(`../src/${name}/devcontainer-template.json`, "utf8")
      );
      const readme = await readFile(`../src/${name}/README.md`, "utf8").catch(
        () => undefined
      );
      template.readme = readme;
      template.readmeHTML = marked(readme);
      templates.push(template);
    }
    return templates;
  });

  return options;
};
