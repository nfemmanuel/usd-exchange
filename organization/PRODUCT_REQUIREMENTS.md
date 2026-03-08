# USD Exchange — Product Requirements

## Goal
Build a tool that imports a USD file into a Metaverse Spatial Fabric map service — architected so it can evolve into a live bidirectional sync between a USD stage and a running spatial fabric.

## Vision
A developer open their USD scene in any DCC tool (Blender, Omniverse, Maya) and the metaverse updates in real-time. Edit a building's position in Blender, it moves in the spatial fabric instantly. The USD file becomes the source of truth for metaverse world building.

## System Requirements
### Functional
- Parse a `.usd`/`.usda` file and extract their prims (objects), their transforms, and metadata
- Map USD prims to MSF map service objects
- Write those objects to a running spatial fabric via ManifolderClient
- Handle updates (idempotent writes — no duplicates on re-import)
### Non-Functional
- Pipeline stages are decoupled (read → transform → write)
- Mapping logic is stateless and reusable (so it can be called on file load or on live change events)
- No hardcoded one-shot assumptions
### Out of Scope for Hackathon
- USD change listeners / real-time trigger
- Bidirectional sync (MSF → USD)
- Complex USD features (animations, variants, physics)

## Open Problems
- **Authorization** — who has write access to a spatial fabric? Stubbing DIDs 
  (author keypairs, signed writes) for now. Real DID infrastructure is future work.
- **Conflict resolution** — simultaneous edits to the same object; USD layer 
  ordering has opinions, MSF may not yet.
- **Scale units** — USD defaults to centimeters, geospatial systems use meters. 
  Needs explicit conversion at the mapping layer.
- **Prim filtering** — clear rules needed for what gets imported (meshes, 
  transforms) vs. ignored (cameras, lights, render settings).

## Future Roadmap
### Phase 2 — Live Sync
- USD change listeners (`Tf.Notice`) trigger incremental MSF updates
- Bidirectional sync (MSF → USD)
- Real-time conflict resolution strategy

### Phase 3 — Real-World Ingestion
- LiDAR / photogrammetry scan → USD → MSF pipeline
- Sources: RealityCapture, Polycam, iPhone LiDAR (all export USD/USDZ natively)
- Same import pipeline, new source

### Phase 4 — Authorization & Identity
- Real DID integration for write authentication
- Per-object ownership and change attribution
- Staged commits (preview before pushing to live fabric)

## Known Open Questions
- What is the full MSF object schema? (blocked until Manifolder repos are read)
- HSML/HSTP role in this stack? (needs clarification)