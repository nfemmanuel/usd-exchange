// Write mapped USD objects into MSF using the Manifolder Promise client.

import "../vendor/ManifolderClient/node/mv-loader.js";
import { createManifolderPromiseClient } from "../vendor/ManifolderClient/ManifolderClient.js";
import { assertSigned, signPayload } from "./did_stub.mjs";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
globalThis.__manifolderUnsafeHosts.add("localhost");
globalThis.__manifolderUnsafeHosts.add("localhost:2000");

function getErrorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

async function openFirstScene(client, scopeId) {
  const scenes = await client.listScenes({ scopeId });
  if (scenes.length === 0) {
    throw new Error("No scenes available in fabric.");
  }
  await client.openScene({ scopeId, sceneId: scenes[0].id });
  return scenes[0];
}

function toCreateParams(scopeId, mappedObject) {
  const { name, objectType, position, rotation, scale, bound, resourceReference, resourceName } = mappedObject;
  return {
    scopeId,
    parentId: "root",
    name,
    objectType,
    position,
    rotation,
    scale,
    bound,
    resourceReference,
    resourceName,
  };
}

export async function writePrims(msfObjects, fabricUrl, adminKey, identity) {
  const client = createManifolderPromiseClient();
  const root = await client.connectRoot({ fabricUrl, adminKey });
  console.log(`[MSF] Connected to fabric, scopeId: ${root.scopeId}`);
  const scene = await openFirstScene(client, root.scopeId);
  console.log(`[MSF] Opened scene: ${scene.name} (id: ${scene.id})`);
  if (!identity) {
    console.warn("[MSF] Warning: writing without author identity (unsigned)");
  }
  const created = [];
  for (const object of msfObjects) {
    console.log(`[MSF] Creating: ${object.name}`);
    try {
      if (identity) {
        const signedPayload = signPayload(object, identity.privateKey);
        assertSigned(signedPayload, identity.publicKey);
        object._did = signedPayload.did;
        object._signature = signedPayload.signature;
        console.log(`[DID] Author: ${signedPayload.did}`);
        console.log(`[DID] Signature: ${signedPayload.signature}`);
      }
      const result = await client.createObject(toCreateParams(root.scopeId, object));
      console.log(`[MSF] Created: ${object.name} -> ${result.id}`);
      created.push({ usd_path: object._usd_path ?? null, msf_id: result.id });
    } catch (error) {
      console.error(`[MSF] ERROR: ${object.name} -> ${getErrorMessage(error)}`);
    }
  }
  console.log(`[MSF] Done. ${created.length} objects written.`);
  return created;
}
