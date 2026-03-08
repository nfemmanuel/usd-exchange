usd-gem-vault.lovable.app
The problem:

Every metaverse platform today is an island. You build in one tool, you're stuck in one world. There's no standard way to take a 3D scene — something you've already built — and put it into a live, shared metaverse space. The Open Metaverse is supposed to fix that, but the tooling doesn't exist yet.

What we built:

USD Exchange. One command. Drop a USD file, watch it appear in the metaverse.

USD — Universal Scene Description — is the lingua franca of 3D. Pixar invented it. Apple uses it. NVIDIA built Omniverse on it. Every major DCC tool — Blender, Maya, Houdini — exports it. It is the closest thing the 3D world has to a universal format.

We built a pipeline that reads a USD file, extracts every object and its world-space transform, and writes it into a live MSF spatial fabric — in real time, over a WebSocket, with author identity on every write.

You run one command. Six objects. Six signed writes. Six objects in the metaverse. Done.

Why it matters:

What you're looking at is Phase 1. A one-shot import. But the architecture is intentionally decoupled — reader, mapper, writer — because Phase 2 is live sync. USD has a built-in change notification system called Tf.Notice. You swap the one-shot read for a change listener, and now when an artist moves an object in Blender, the metaverse updates in real time. The USD file becomes the source of truth for the world.

Phase 3 is real-world ingestion. LiDAR scan a building, photogrammetry a city block, pipe it through USD into the fabric. Physical spaces become metaverse spaces automatically.

Phase 4 is ownership. Right now our DID layer is a stub — ed25519 keypairs, every write signed, every object has an author. Swap the stub for real W3C DIDs and you have provable, on-chain ownership of every object in the metaverse. Not just who made it — who owns it, who can edit it, who can monetize it.

What we're asking:

We built the core loop in one day, on open standards, on top of the MSF spec. The pipeline works. The vision is real. We want to keep building.




