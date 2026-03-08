import '../vendor/ManifolderClient/node/mv-loader.js';
import { createManifolderPromiseClient } from '../vendor/ManifolderClient/ManifolderClient.js';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
globalThis.__manifolderUnsafeHosts.add('localhost');

const client = createManifolderPromiseClient();

console.log('Connecting to local fabric...');

const root = await client.connectRoot({
    fabricUrl: 'https://localhost:2000/fabric/',
    adminKey: 'localdevpassword',
});

console.log('Connected! scopeId:', root.scopeId);

const scenes = await client.listScenes({ scopeId: root.scopeId });
console.log('Scenes:', scenes);