// Orchestrate USD->MSF import by calling Python mapping and then MSF writer.

import { spawn } from "node:child_process";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { loadOrCreateIdentity } from "./did_stub.mjs";
import { writePrims } from "./msf_writer.mjs";

const DEFAULT_FABRIC_URL = "https://localhost:2000/fabric/";
const DEFAULT_ADMIN_KEY = "localdevpassword";
const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const IDENTITY_PATH = resolve(PROJECT_ROOT, ".identity.json");

async function readStream(stream) {
  let output = "";
  for await (const chunk of stream) {
    output += chunk.toString();
  }
  return output;
}

function parseMapperOutput(rawOutput) {
  try {
    return JSON.parse(rawOutput);
  } catch (error) {
    throw new Error(`Failed to parse mapper JSON: ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function runMapper(usdaPath) {
  const child = spawn("python", ["scripts/run_mapper.py", usdaPath], {
    stdio: ["ignore", "pipe", "pipe"],
  });
  const stdoutPromise = readStream(child.stdout);
  const stderrPromise = readStream(child.stderr);
  const [exitCode] = await once(child, "close");
  const [stdout, stderr] = await Promise.all([stdoutPromise, stderrPromise]);
  if (stderr) {
    process.stderr.write(stderr);
  }
  if (exitCode !== 0) {
    throw new Error(`Mapper process failed with exit code ${exitCode}`);
  }
  return parseMapperOutput(stdout);
}

async function main() {
  const usdaPath = process.argv[2];
  if (!usdaPath) {
    throw new Error("Usage: node src/import_usd.mjs <usda_path>");
  }
  console.log(`[PIPELINE] Starting import: ${usdaPath}`);
  const mappedObjects = await runMapper(usdaPath);
  console.log(`[PIPELINE] Read ${mappedObjects.length} objects from USD`);
  const identity = loadOrCreateIdentity(IDENTITY_PATH);
  console.log(`[PIPELINE] Author identity: ${identity.did}`);
  await writePrims(mappedObjects, DEFAULT_FABRIC_URL, DEFAULT_ADMIN_KEY, identity);
  console.log("[PIPELINE] Import complete.");
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`[PIPELINE] ERROR: ${message}`);
  process.exit(1);
});
