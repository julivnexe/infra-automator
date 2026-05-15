#!/usr/bin/env bash
# ============================================================================
# infra-automator — shell hardening fallback
#
# Used when Ansible isn't installed locally. Same end-state as the Ansible
# playbook, but a single self-contained script suitable for rescue / bring-up.
#
# Inputs (env vars):
#   ADMIN_USER         : non-root username to create (default: deploy)
#   ADMIN_PUBKEY       : OpenSSH-format public key to install for ADMIN_USER
#   SSH_PORT           : sshd listen port (default: 22)
#   EXTRA_OPEN_PORTS   : comma-separated extra TCP ports to allow in UFW
#
# Designed for Ubuntu 22.04 / Debian 12. Idempotent.
# ============================================================================

set -euo pipefail

ADMIN_USER="${ADMIN_USER:-deploy}"
SSH_PORT="${SSH_PORT:-22}"
ADMIN_PUBKEY="${ADMIN_PUBKEY:-}"
EXTRA_OPEN_PORTS="${EXTRA_OPEN_PORTS:-}"

log() { printf '\033[36m[harden]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[harden]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "must run as root"
[[ -n "$ADMIN_PUBKEY" ]] || die "ADMIN_PUBKEY is required"

export DEBIAN_FRONTEND=noninteractive

# --- 1. Base packages -------------------------------------------------------
log "updating apt cache + installing base packages"
apt-get update -qq
apt-get install -y -qq \
    ca-certificates curl gnupg htop ufw fail2ban \
    unattended-upgrades apt-listchanges tzdata

# --- 2. Unattended security upgrades ----------------------------------------
log "enabling unattended security upgrades"
cat >/etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF

# --- 3. Admin user ----------------------------------------------------------
if ! id -u "$ADMIN_USER" >/dev/null 2>&1; then
    log "creating admin user '$ADMIN_USER'"
    useradd -m -s /bin/bash -G sudo "$ADMIN_USER"
fi

log "configuring passwordless sudo"
install -m 0440 /dev/stdin "/etc/sudoers.d/90-${ADMIN_USER}" <<<"$ADMIN_USER ALL=(ALL) NOPASSWD:ALL"
visudo -cf "/etc/sudoers.d/90-${ADMIN_USER}" >/dev/null

log "installing authorized_keys for $ADMIN_USER"
install -d -m 0700 -o "$ADMIN_USER" -g "$ADMIN_USER" "/home/${ADMIN_USER}/.ssh"
printf '%s\n' "$ADMIN_PUBKEY" >"/home/${ADMIN_USER}/.ssh/authorized_keys"
chown "${ADMIN_USER}:${ADMIN_USER}" "/home/${ADMIN_USER}/.ssh/authorized_keys"
chmod 0600 "/home/${ADMIN_USER}/.ssh/authorized_keys"

# --- 4. SSH hardening -------------------------------------------------------
log "hardening sshd on port ${SSH_PORT}"
mkdir -p /etc/ssh/sshd_config.d
cat >/etc/ssh/sshd_config.d/99-hardening.conf <<EOF
Port ${SSH_PORT}
PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication no
KbdInteractiveAuthentication no
UsePAM yes
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
LoginGraceTime 30
AllowUsers ${ADMIN_USER}
EOF
sshd -t
systemctl restart ssh

# --- 5. UFW -----------------------------------------------------------------
log "configuring UFW (default deny in, allow out)"
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw limit "${SSH_PORT}/tcp"
ufw allow 80/tcp
ufw allow 443/tcp
if [[ -n "$EXTRA_OPEN_PORTS" ]]; then
    IFS=',' read -ra _ports <<<"$EXTRA_OPEN_PORTS"
    for p in "${_ports[@]}"; do
        ufw allow "${p}/tcp"
    done
fi
ufw logging low
ufw --force enable

# --- 6. fail2ban ------------------------------------------------------------
log "configuring fail2ban (sshd jail)"
cat >/etc/fail2ban/jail.d/sshd.local <<EOF
[sshd]
enabled = true
port    = ${SSH_PORT}
filter  = sshd
logpath = %(sshd_log)s
backend = %(sshd_backend)s
maxretry = 4
findtime = 10m
bantime  = 1h
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban

# --- 7. Docker --------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    log "installing Docker CE"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        >/etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
    usermod -aG docker "$ADMIN_USER"
fi

log "writing Docker daemon defaults (log rotation, live-restore)"
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "live-restore": true
}
EOF
systemctl enable docker
systemctl restart docker

log "✓ hardening complete"
