// Provide a lightweight DID-style identity, signing, and verification stub for pipeline demos.

import { createPrivateKey, createPublicKey, generateKeyPairSync, sign, verify } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const keyDidRegistry = new WeakMap();

function canonicalizeJson(value) {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((entry) => canonicalizeJson(entry)).join(",")}]`;
  }
  const keys = Object.keys(value).sort();
  const body = keys.map((key) => `${JSON.stringify(key)}:${canonicalizeJson(value[key])}`).join(",");
  return `{${body}}`;
}

function base64UrlToHex(value) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
  return Buffer.from(padded, "base64").toString("hex");
}

function deriveDidFromPublicKey(publicKey) {
  const jwk = publicKey.export({ format: "jwk" });
  if (!jwk.x) {
    throw new Error("Unable to derive DID: public key missing JWK x coordinate.");
  }
  const publicKeyHex = base64UrlToHex(jwk.x);
  return `did:stub:${publicKeyHex.slice(0, 16)}`;
}

function registerIdentityKeys(did, publicKey, privateKey) {
  keyDidRegistry.set(publicKey, did);
  keyDidRegistry.set(privateKey, did);
}

function exportIdentityPem(identity) {
  return {
    did: identity.did,
    publicKeyPem: identity.publicKey.export({ type: "spki", format: "pem" }),
    privateKeyPem: identity.privateKey.export({ type: "pkcs8", format: "pem" }),
  };
}

function importIdentityPem(storedIdentity) {
  const publicKey = createPublicKey(storedIdentity.publicKeyPem);
  const privateKey = createPrivateKey(storedIdentity.privateKeyPem);
  const did = deriveDidFromPublicKey(publicKey);
  registerIdentityKeys(did, publicKey, privateKey);
  return { did, publicKey, privateKey };
}

function getPayloadName(payload) {
  return payload?.name ?? "unknown";
}

export function generateAuthorIdentity() {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const did = deriveDidFromPublicKey(publicKey);
  registerIdentityKeys(did, publicKey, privateKey);
  return { did, publicKey, privateKey };
}

export function loadOrCreateIdentity(identityPath) {
  if (existsSync(identityPath)) {
    const stored = JSON.parse(readFileSync(identityPath, "utf8"));
    const identity = importIdentityPem(stored);
    if (stored.did !== identity.did) {
      writeFileSync(identityPath, `${JSON.stringify(exportIdentityPem(identity), null, 2)}\n`, "utf8");
    }
    console.log(`[DID] Loaded identity: ${identity.did}`);
    return identity;
  }
  const identity = generateAuthorIdentity();
  mkdirSync(dirname(identityPath), { recursive: true });
  writeFileSync(identityPath, `${JSON.stringify(exportIdentityPem(identity), null, 2)}\n`, "utf8");
  console.log(`[DID] Generated new identity: ${identity.did}`);
  return identity;
}

export function signPayload(payload, privateKey) {
  const did = keyDidRegistry.get(privateKey) || "did:stub:unknown";
  console.log(`[DID] Signing payload for: ${getPayloadName(payload)}`);
  const canonicalJson = canonicalizeJson(payload);
  const signature = sign(null, Buffer.from(canonicalJson), privateKey).toString("hex");
  return { payload, signature, did };
}

export function verifyPayload(payload, signature, publicKey) {
  const canonicalJson = canonicalizeJson(payload);
  const valid = verify(null, Buffer.from(canonicalJson), publicKey, Buffer.from(signature, "hex"));
  const verdict = valid ? "VALID" : "INVALID";
  console.log(`[DID] Signature ${verdict} for: ${getPayloadName(payload)}`);
  return valid;
}

export function assertSigned(signedPayload, publicKey) {
  const payload = signedPayload?.payload;
  const signature = signedPayload?.signature;
  const name = getPayloadName(payload || signedPayload);
  if (!payload || typeof signature !== "string" || !verifyPayload(payload, signature, publicKey)) {
    throw new Error(`Unsigned or invalid payload rejected: ${name}`);
  }
}
