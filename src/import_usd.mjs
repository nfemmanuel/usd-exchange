// Pipeline entry point: USD file -> Python mapper -> MSF fabric writer
// Also serves public/meshes/ as static HTTPS so the fabric can load .glb resourceReferences.

import { spawn } from "child_process";
import { readFileSync, existsSync } from "fs";
import { createServer } from "https";
import { readFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { writePrims } from "./msf_writer.mjs";
import { loadOrCreateIdentity } from "./did_stub.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..");

const FABRIC_URL = "https://localhost:2000/fabric/";
const ADMIN_KEY = "localdevpassword";
const MESH_SERVER_PORT = 2001; // separate port for our static .glb server
const STATIC_BASE_URL = `https://localhost:${MESH_SERVER_PORT}/meshes`;

// SSL cert reuse from MSF_Map_Svc (self-signed, same host)
const SSL_KEY = path.join(PROJECT_ROOT, "MSF_Map_Svc", "dist", "ssl", "server.key");
const SSL_CERT = path.join(PROJECT_ROOT, "MSF_Map_Svc", "dist", "ssl", "server.cert");

function startMeshServer() {
  if (!existsSync(SSL_KEY) || !existsSync(SSL_CERT)) {
    console.warn("[MESH_SVC] SSL certs not found, skipping static mesh server.");
    return null;
  }

  const options = {
    key: readFileSync(SSL_KEY),
    cert: readFileSync(SSL_CERT),
  };

  const server = createServer(options, async (req, res) => {
    // Only serve /meshes/*.glb
    const url = req.url || "/";
    if (!url.startsWith("/meshes/")) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    const filename = path.basename(url);
    const filePath = path.join(PROJECT_ROOT, "public", "meshes", filename);
    try {
      const data = await readFile(filePath);
      res.writeHead(200, {
        "Content-Type": "model/gltf-binary",
        "Access-Control-Allow-Origin": "*",
      });
      res.end(data);
    } catch {
      res.writeHead(404);
      res.end("Not found");
    }
  });

  server.listen(MESH_SERVER_PORT, () => {
    console.log(`[MESH_SVC] Serving .glb files at https://localhost:${MESH_SERVER_PORT}/meshes/`);
  });

  return server;
}

function runMapper(usdPath) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(PROJECT_ROOT, "scripts", "run_mapper.py");
    const proc = spawn("python", [scriptPath, usdPath], { cwd: PROJECT_ROOT });

    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => (stdout += d.toString()));
    proc.stderr.on("data", (d) => {
      const line = d.toString();
      stderr += line;
      process.stderr.write(line);
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Mapper exited with code ${code}\n${stderr}`));
        return;
      }
      try {
        // Extract JSON array from stdout (may have [USD]/[MAP] log lines mixed in)
        const jsonMatch = stdout.match(/(\[[\s\S]*\])\s*$/);
        if (!jsonMatch) throw new Error("No JSON array found in mapper output");
        resolve(JSON.parse(jsonMatch[1]));
      } catch (e) {
        reject(new Error(`Failed to parse mapper output: ${e.message}\n${stdout}`));
      }
    });
  });
}

async function main() {
  const usdPath = process.argv[2];
  if (!usdPath) {
    console.error("Usage: node src/import_usd.mjs <path/to/file.usd>");
    process.exit(1);
  }

  const absUsdPath = path.resolve(usdPath);
  console.log(`[PIPELINE] Starting import: ${usdPath}`);

  // Start static mesh server
  const meshServer = startMeshServer();

  // Run Python pipeline
  const msfObjects = await runMapper(absUsdPath);
  console.log(`[PIPELINE] Read ${msfObjects.length} objects from USD`);

  // Log which objects have mesh references
  for (const obj of msfObjects) {
    if (obj.resourceReference) {
      console.log(`[PIPELINE] Mesh asset: ${obj.name} -> ${obj.resourceReference}`);
    }
  }

  // Load DID identity
  const identityPath = path.join(PROJECT_ROOT, ".identity.json");
  const identity = await loadOrCreateIdentity(identityPath);
  console.log(`[DID] Loaded identity: ${identity.did}`);
  console.log(`[PIPELINE] Author identity: ${identity.did}`);

  // Write to fabric
  await writePrims(msfObjects, FABRIC_URL, ADMIN_KEY, identity);

  // Shut down mesh server cleanly
  if (meshServer) {
    meshServer.close(() => {
      console.log("[MESH_SVC] Stopped.");
    });
  }

  console.log("[PIPELINE] Import complete.");
  process.exit(0);
}

main().catch((err) => {
  console.error("[PIPELINE] Fatal error:", err);
  process.exit(1);
});
