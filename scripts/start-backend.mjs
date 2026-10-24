import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
if (!existsSync(python)) {
  console.error('Create the project .venv with Python 3.12+ and install backend[server] first.');
  process.exit(1);
}
const args = [
  '-m', 'uvicorn', 'app.main:create_app', '--factory', '--app-dir', 'backend',
  '--host', process.env.HOST || '127.0.0.1', '--port', process.env.PORT || '8000',
];
for (const file of ['.env.local', '.env']) {
  if (existsSync(path.join(root, file))) {
    args.push('--env-file', file);
    break;
  }
}
const server = spawn(python, args, {
  cwd: root,
  stdio: 'inherit',
  env: {
    ...process.env,
    SERVE_FRONTEND: process.env.SERVE_FRONTEND || 'true',
    OE_DATA_DIR: process.env.OE_DATA_DIR || path.join(root, '.local-data'),
  },
});
server.on('error', (error) => { console.error(error.message); process.exitCode = 1; });
server.on('exit', (code) => { process.exitCode = code ?? 1; });
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => server.kill(signal));
}
