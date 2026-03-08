# USD Exchange — Developer Backlog
This backlog tracks the development of the USD Exchange tool for the Open Metaverse Hackathon. The immediate priority is Epics 1 and 2 — environment setup and research spikes — as all pipeline work is blocked until we understand the MSF object schema and can confirm our local fabric is running. Epics are ordered by dependency, not necessarily by team member. Split accordingly once skills are established.

## Epics Table of Contents
- [Epic 1: Environment Setup](#epic-1-environment-setup)
- [Epic 2: Research Spike](#epic-2-research-spike)
- [Epic 3: Core Import Pipeline](#epic-3-core-import-pipeline)
- [Epic 4: DID Stub (Auth)](#epic-4-did-stub-auth)
- [Epic 5: Demo & Presentation](#epic-5-demo--presentation)

---

## Epic 1: Environment Setup

### 1.1 Python Environment
- [x] 1.1.1 Install Python 3.11
- [x] 1.1.2 Create `.venv` in project folder
- [x] 1.1.3 Install `usd-core`
- [x] 1.1.4 Verify with a simple stage open script

### 1.2 Repo Setup
- [x] 1.2.1 Clone Manifolder, ManifolderClient, ManifolderMCP
- [x] 1.2.2 Get a local fabric server running
- [ ] 1.2.3 Confirm ManifolderClient can connect to it

---

## Epic 2: Research Spike

### 2.1 USD Traversal
- [ ] 2.1.1 Load a sample `.usda` file
- [ ] 2.1.2 Traverse the prim tree
- [ ] 2.1.3 Extract transforms (position, rotation, scale) from a prim
- [ ] 2.1.4 Identify how meshes and metadata are stored

### 2.2 MSF Schema Mapping
- [ ] 2.2.1 Read Manifolder source to understand the map service object structure
- [ ] 2.2.2 Document what fields an MSF object has
- [ ] 2.2.3 Identify the minimum viable fields needed for a basic import

### 2.3 ManifolderClient API
- [ ] 2.3.1 Read ManifolderClient docs/source
- [ ] 2.3.2 Understand how to write an object to a fabric
- [ ] 2.3.3 Understand how updates/deletes work (idempotency)

---

## Epic 3: Core Import Pipeline

### 3.1 USD Reader
- [ ] 3.1.1 Traverse stage and collect all mesh prims
- [ ] 3.1.2 Extract transform per prim
- [ ] 3.1.3 Apply scale unit conversion (cm → m)
- [ ] 3.1.4 Filter out non-importable prims (cameras, lights, render settings)

### 3.2 Mapping Layer
- [ ] 3.2.1 Define a neutral internal object schema (USD prim → intermediate representation)
- [ ] 3.2.2 Map intermediate representation → MSF object
- [ ] 3.2.3 Handle prim naming / unique ID generation

### 3.3 MSF Writer
- [ ] 3.3.1 Write a single object to a running fabric
- [ ] 3.3.2 Write a full scene (batch)
- [ ] 3.3.3 Idempotent update (re-import same scene, no duplicates)

---

## Epic 4: DID Stub (Auth)

### 4.1 Author Identity
- [ ] 4.1.1 Generate a simple keypair per "author"
- [ ] 4.1.2 Sign each write operation with author key
- [ ] 4.1.3 Fabric write layer rejects unsigned payloads
- [ ] 4.1.4 Log author attribution per object

---

## Epic 5: Demo & Presentation

### 5.1 Sample USD File
- [ ] 5.1.1 Find or create a simple `.usda` test scene (a few objects with transforms)

### 5.2 Demo Script
- [ ] 5.2.1 CLI or simple UI to trigger import
- [ ] 5.2.2 Show before/after in Manifolder visualizer

### 5.3 Pitch
- [ ] 5.3.1 Clearly communicate the vision (Phase 2–4 roadmap)
- [ ] 5.3.2 Prepare architecture diagram