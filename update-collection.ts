#!/usr/bin/env -S deno run -A
import { copyFile, readFile, writeFile } from "node:fs/promises";
import { $ } from "npm:zx";
import { temporaryDirectory, temporaryWrite } from "npm:tempy";
import process from "node:process";
import { join } from "node:path";

async function getAllTemplates(repo: string): Promise<string[]> {
  const [owner, name] = repo.split("/");
  const url = new URL("https://github.com/search");
  url.searchParams.set(
    "q",
    `owner:${owner} /${name}\\/.+/ package_type:container`
  );
  url.searchParams.set("type", "registrypackages");
  const response = await fetch(url);
  return (await response.json()).payload.results
    .map((x) => x.name)
    .filter((f) => f !== name)
    .map((f) => f.split("/")[1]);
}

async function getTemplateManifest(image: string): Promise<any> {
  if (!image.endsWith(":latest")) {
    image += ":latest";
  }

  const tempDirPath = temporaryDirectory()
  const oldCWD = $.cwd
  $.cwd = tempDirPath
  let templateManifest: any
  try {
    await $`oras pull ${image}`
    templateManifest = JSON.parse(await readFile(join($.cwd, "devcontainer-template.json")))
  } finally {
    $.cwd = oldCWD
  }
  return templateManifest
}

const devcontainerCollection = {
  sourceInformation: {
    source: "devcontainer-cli",
  },
  templates: [] as any[],
};
const featureIds = await getAllTemplates(process.env.GITHUB_REPOSITORY!);
for (const id of featureIds) {
  const devcontainerTemplate = await getTemplateManifest(
    `ghcr.io/${process.env.GITHUB_REPOSITORY}/${id}`
  );
  devcontainerCollection.templates.push(devcontainerTemplate);
}

const seenIds = new Set()
for (let i = 0; i < devcontainerCollection.templates.length; i++) {
  const f = devcontainerCollection.templates[i]
  if (seenIds.has(f.id)) {
    devcontainerCollection.templates.splice(i, 1);
    i--;
  } else {
    seenIds.add(f.id)
  }
}

const tempDirPath = temporaryDirectory();
process.chdir(tempDirPath);
$.cwd = process.cwd();

await writeFile(
  "devcontainer-collection.json",
  JSON.stringify(devcontainerCollection, null, 2)
);

const annotations = {
  $manifest: {
    "com.github.package.type": "devcontainer_collection",
  },
  "devcontainer-collection.json": {
    "org.opencontainers.image.title": "devcontainer-collection.json",
  },
};
const annotationsPath = await temporaryWrite(
  JSON.stringify(annotations, null, 2),
  { suffix: ".json" }
);

await $`tree -a`;

await $`oras push \
  ghcr.io/${process.env.GITHUB_REPOSITORY}:latest \
  --config /dev/null:application/vnd.devcontainers \
  --annotation-file ${annotationsPath} \
  devcontainer-collection.json:application/vnd.devcontainers.collection.layer.v1+json`;
