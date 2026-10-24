#!/usr/bin/env bash
# Run only on the new dedicated Ubuntu 24.04 Oracle instance, as root.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo 'Run with sudo on the Oracle instance.' >&2
  exit 1
fi
source /etc/os-release
if [[ ${ID} != ubuntu || ${VERSION_ID} != 24.04 ]]; then
  echo 'This installer requires Ubuntu 24.04.' >&2
  exit 1
fi
app_dir=/opt/openconstructionerp/app
env_file=/etc/openconstructionerp/environment
test -f "${app_dir}/backend/pyproject.toml"
test -f "${app_dir}/frontend/dist/index.html"
test -s "${env_file}"
# Check only key names. Never print database credentials to deployment logs.
grep -q '^DATABASE_URL=' "${env_file}"
grep -q '^JWT_SECRET=' "${env_file}"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3.12 python3.12-venv libpq-dev build-essential ca-certificates
if ! id openconstructionerp >/dev/null 2>&1; then
  useradd --system --user-group --home-dir /var/lib/openconstructionerp --shell /usr/sbin/nologin openconstructionerp
fi
install -d -m 0700 -o openconstructionerp -g openconstructionerp /var/lib/openconstructionerp
chown root:root "${env_file}"
chmod 0600 "${env_file}"
python3.12 -m venv /opt/openconstructionerp/venv
/opt/openconstructionerp/venv/bin/python -m pip install --upgrade pip
/opt/openconstructionerp/venv/bin/python -m pip install -e "${app_dir}/backend[server,semantic-clients]"
install -m 0644 "${app_dir}/deploy/oracle/openconstructionerp.service" /etc/systemd/system/openconstructionerp.service
systemctl daemon-reload
systemctl enable --now openconstructionerp.service
echo 'Backend started on loopback port 8000; wait for initialization before health checks.'
echo 'Public routing and HTTPS must be configured separately after the health check passes.'
