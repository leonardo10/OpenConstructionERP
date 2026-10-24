# Oracle Always Free deployment preparation

Target: dedicated Ubuntu 24.04 ARM instance, VM.Standard.A1.Flex, 2 OCPUs,
12 GB RAM, 50 GB boot volume in the tenancy home region (Singapore).
Confirm remaining account quotas and Always Free eligibility before launch.
No instance has been created by preparing these files.

Use the fork's source code, including its Neon connection fixes, under
`/opt/openconstructionerp/app`. Extract the verified GitHub frontend artifact
under `frontend/dist` before installing Python dependencies. Building the UI
again on the instance is unnecessary.

Install production settings privately at `/etc/openconstructionerp/environment`
with mode 0600. Use the existing Neon pooled application URL, direct migration
URL, JWT secret and production settings. Never upload this file to GitHub or
paste its contents in Cloud Shell/browser command history. Transfer secrets
over SSH once the instance host key has been verified.

Run `sudo bash /opt/openconstructionerp/app/deploy/oracle/install-backend.sh`.
The service binds to loopback port 8000 and stores uploads in
`/var/lib/openconstructionerp`. It starts automatically after reboot.
The installer does not open network ports or configure public HTTP/HTTPS.

Check `http://127.0.0.1:8000/api/health` on the server and require
`database=ok` and `status=healthy` before adding public routing. Complete the
first-admin bootstrap through a private SSH tunnel before exposing the app.
Review allowed origins and HTTPS against the actual chosen hostname.

Python package availability on Linux ARM was checked for the required embedded
Postgres dependency (pixeltable-pgserver 0.5.1 has a CPython 3.12 aarch64 wheel).
The complete installation and BIM runtime still require verification on the
actual Oracle instance. No unverified compatibility is claimed here.
