# USD Exchange

USD Exchange is a hackathon project built at the First Annual Open Metaverse Hackathon (March 2026), hosted by RP1 and the Metaverse Standards Forum.

**One-line pitch:** "Drop a USD file. Watch it appear in the metaverse."

The current implementation is a USD-to-Metaverse import pipeline. It opens a `.usda` scene, traverses the prim hierarchy, computes world-space transforms, maps those prims to MSF object payloads, and writes them into a live spatial fabric through ManifolderClient. Each write operation is signed with a lightweight DID stub (Ed25519) to show author attribution and payload verification.

## Stack

The pipeline is split across Python and Node.js. Python with `usd-core` (`pxr`) handles USD parsing and transform extraction. Node.js ES modules handle orchestration, identity, signing, and writes to fabric. ManifolderClient (Patched Reality) is the connectivity layer to MSF_Map_Svc (Metaversal Corp), backed by MySQL.

## Repository Layout

```text
src/
  usd_reader.py       # Python: opens USD stage, traverses prims, extracts transforms
  mapper.py           # Python: maps USD prims to MSF CreateObjectParams
  msf_writer.mjs      # Node.js: connects to fabric, writes objects via ManifolderClient
  import_usd.mjs      # Node.js: pipeline entry point, spawns Python subprocess
  did_stub.mjs        # Node.js: keypair generation, payload signing, verification
scripts/
  run_mapper.py       # Python subprocess shim: outputs mapped prims as JSON to stdout
  usd_traverse.py     # Research spike: USD traversal explorer
  test_manifolder_connect.mjs  # Research spike: ManifolderClient connectivity test
  verify_usd.py       # Environment check: verifies usd-core is installed
samples/
  sample.usda         # Sample USD scene: World > Building (Roof, Walls), Tree (Trunk)
vendor/
  ManifolderClient/   # git submodule - Patched Reality
  Manifolder/         # git submodule - Patched Reality
  ManifolderMCP/      # git submodule - Patched Reality
MSF_Map_Svc/          # git submodule - Metaversal Corp
organization/
  PRODUCT_REQUIREMENTS.md
  BACKLOG.md
```

## Running the Pipeline

Prerequisites are Python 3.11+, Node.js 18+, MySQL, and a running `MSF_Map_Svc` instance. Create a Python virtual environment, install `usd-core`, and make sure Node dependencies (`socket.io-client`, `ws`) are available.

Run a full import with:

```bash
node src/import_usd.mjs samples/sample.usda
```

`import_usd.mjs` spawns the Python mapper (`scripts/run_mapper.py`), parses mapped JSON from stdout, loads or creates `.identity.json` for author identity, then writes objects into the first available scene in the target fabric.

## Demo Output

```text
[PIPELINE] Starting import: samples/sample.usda
[USD] Opening stage: ...sample.usda
[USD] Traversed 6 prims
[USD] Kept 6 supported prims
[MAP] Mapping prim: /World -> World
[MAP] Mapping prim: /World/Building -> Building
[MAP] Mapping prim: /World/Building/Roof -> Roof
[MAP] Mapping prim: /World/Building/Walls -> Walls
[MAP] Mapping prim: /World/Tree -> Tree
[MAP] Mapping prim: /World/Tree/Trunk -> Trunk
[PIPELINE] Read 6 objects from USD
[DID] Loaded identity: did:stub:3e4eb3a3187db63b
[PIPELINE] Author identity: did:stub:3e4eb3a3187db63b
[MSF] Connected to fabric, scopeId: 1_10b8219d8c888e37
[MSF] Opened scene: My First Scene (id: physical:1)
[MSF] Creating: World
[DID] Signing payload for: World
[DID] Signature VALID for: World
[MSF] Created: World -> physical:5
...
[MSF] Done. 6 objects written.
[PIPELINE] Import complete.
```

## Debug Log Conventions

- `[USD]` for USD reader messages
- `[MAP]` for mapping layer messages
- `[MSF]` for fabric writer messages
- `[DID]` for identity and signing messages
- `[PIPELINE]` for top-level orchestration messages

## Roadmap

1. Phase 1 (done): One-shot USD import to spatial fabric.
2. Phase 2: Live sync. USD change listeners (`Tf.Notice`) trigger incremental MSF updates in real time so artist edits can appear instantly.
3. Phase 3: Real-world ingestion. LiDAR and photogrammetry pipelines convert physical spaces into USD, then into MSF.
4. Phase 4: Real DID auth. Move from stub signing to W3C DID, per-object on-chain ownership, staged commits, and provable authorship.

USD Exchange is still a hackathon build, but the pipeline already proves the central interaction loop: authored 3D scene data can be transformed, attributed, and published into a live metaverse fabric with a single command.
