# Pi 3 A+ setup: blank card to commissioned kiosk

This walkthrough targets your **Raspberry Pi 3 Model A+ Rev 1.1, 512 MB**, HDMI display and four level sensors. Use **official Raspberry Pi OS Lite (64-bit), Trixie, arm64 userspace**. It is a reflash, not an in-place architecture conversion. Official Raspbian Trixie armhf repositories do not provide the required `python3-pyside6` packages; a 64-bit kernel over armhf userspace does not fix that. Debian Trixie publishes the arm64 packages used by the official 64-bit OS repository configuration.

**Nothing here claims a physical pass.** The Pi's graphics, memory headroom, power, keyboard and electrical installation still need measurement. First get a **mock-input display** working with GPIO disconnected. Live boot is the final, separately authorized step.

Detailed contracts: [packages/display](device.md), [service lifecycle and approval](../deploy/systemd/README.md), and [electrical calibration and acceptance](operator.md). Keep a dated private installation record; do not put Wi-Fi passwords, Bluetooth addresses or visitor text in the repository.

## 1. Save anything needed, then flash the right image

1. If the old Pi still runs, copy any wanted files and installation records off it first. Run `sudo poweroff`, wait for shutdown activity to finish, disconnect power, then remove the microSD. Never pull a powered card. If its contents matter, make a full-card backup with a trusted disk-imaging tool and verify a restore onto a spare card before overwriting the original. An empty card needs no data backup.
2. On the Mac, install/open [Raspberry Pi Imager](https://www.raspberrypi.com/software/). Select Raspberry Pi 3 as the device family and **Raspberry Pi OS Lite (64-bit)**. Confirm the selected image is **Trixie**, not a desktop image, Bookworm, or Lite 32-bit. If the catalog changes, select the official Trixie Lite64 image from the [OS downloads](https://www.raspberrypi.com/software/operating-systems/) rather than silently changing this baseline.
3. **Writing erases the entire selected storage device.** Check the microSD's capacity and device identity; unplug unrelated external drives if identification is ambiguous. Do not select the Mac's storage or a backup disk.
4. In Imager customization choose a hostname, for example `thirsty-pi`, and a separate maintenance username, for example `maintainer`. **Do not use `thirsty`**: that name is reserved for the non-root, non-interactive kiosk service. Set a strong maintenance password, locale/timezone and the keyboard layout you actually use. Configure your Wi-Fi SSID/password and correct wireless country (Pi 3 A+ supports both 2.4 GHz and 5 GHz). Enable SSH, preferably with your Mac's public key. Record your actual choices privately.
5. Write and verify the image, eject the card safely, insert it with power disconnected. Attach HDMI, a recovery keyboard if available, and a suitable Pi supply. Leave sensors disconnected. Boot; allow initial setup to finish.

On the Mac, use your chosen username/hostname (the following examples assume the choices above):

```sh
ssh maintainer@thirsty-pi.local
```

If `.local` fails, find the Pi's address in your router's client list or with `hostname -I` on its local console; use that actual address. After reflash, an SSH host-key warning can be legitimate, but verify the Pi/address first before removing only its stale known-host entry. Do not disable host-key checks globally.

On the Pi:

```sh
cat /proc/device-tree/model; echo
cat /etc/os-release
dpkg --print-architecture
getconf LONG_BIT
uname -m
```

Expect the actual Pi 3 Model A Plus board, `VERSION_CODENAME=trixie`, **`arm64`**, and **64**. `uname` alone is insufficient. Stop if these disagree. Use the image's normal KMS configuration; do not paste old `gpu_mem`, FKMS or framebuffer recipes from unrelated guides.

## 2. Transfer this Mac checkout, including your unpushed changes

A GitHub clone **does not include local edits**. Transfer the reviewed working tree from the Mac, including current source, assets and configuration. Do not run the experiment/capture tooling. The allow-list below also avoids transferring generated `output`, workstation dependencies and unrelated materials.

On the **Mac**, from this repository's root, with your actual SSH destination:

```sh
PI=maintainer@thirsty-pi.local
BUNDLE=$(mktemp -d "${TMPDIR:-/tmp}/thirsty-transfer.XXXXXX")
COPYFILE_DISABLE=1 tar \
  --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.pytest_cache' --exclude='.mypy_cache' \
  --exclude='.ruff_cache' --exclude='*.egg-info' --exclude='.DS_Store' \
  --exclude='output' \
  -czf "$BUNDLE/source.tar.gz" \
  app config deploy docs README.md PRODUCT.md DESIGN.md pyproject.toml
shasum -a 256 "$BUNDLE/source.tar.gz"
REMOTE_STAGE=$(ssh "$PI" 'mktemp -d "$HOME/thirsty-stage.XXXXXX"')
printf 'Pi staging directory: %s\n' "$REMOTE_STAGE"
scp "$BUNDLE/source.tar.gz" "$PI:$REMOTE_STAGE/source.tar.gz"
```

Save the printed stage path and hash. These commands transfer files actually on disk; save editor buffers first. On the **Pi**, set `STAGE` to that printed path, not a guessed directory:

```sh
read -r -p 'Paste the Pi staging directory: ' STAGE
sha256sum "$STAGE/source.tar.gz"
mkdir "$STAGE/tree"
tar -xzf "$STAGE/source.tar.gz" -C "$STAGE/tree"
find "$STAGE/tree" -type l -print
```

Compare hashes. The `find` output must be empty: the installed service rejects symlinks. If not, stop and review their sources rather than blindly dereferencing them. Review the transferred config and code. The bundle contains your local four-sensor changes; do not replace them with a stale GitHub copy.

For a **fresh installation only**, install the reviewed tree:

```sh
sudo mkdir /opt/thirsty
sudo cp -R "$STAGE/tree/." /opt/thirsty/
sudo chown -R root:root /opt/thirsty
sudo chmod -R u+rwX,go+rX,go-w /opt/thirsty
cd /opt/thirsty
```

If `mkdir` says `/opt/thirsty` exists, **stop rather than merging**. For an update, stop the existing service, back up its config and private approvals, and move the old tree aside before installing a fresh one. Do not delete an existing installation blindly. `/opt` and the installed tree must be root-controlled; the installer checks ancestors too. `output/app` is deliberately absent/empty, not a transferred generated site. Keep the transfer archive until setup is accepted; store durable backups outside temporary directories.

## 3. Install official packaged dependencies

Use the image's official signed apt sources unchanged. On Lite64 those include the distribution's Debian arm64 packages and Raspberry Pi packages. **Do not add Debian sources to an armhf Raspbian image**, mix releases, install guessed `.deb` files, disable signatures, use pip for Qt/GPIO, or copy the Mac virtualenv. A missing candidate is a stop condition, not permission to improvise a repository.

On the Pi:

```sh
cd /opt/thirsty
sudo apt-get update
bash deploy/setup-device.sh --display-backend wayland
```

This is the plan: target guards, candidate inspection and apt simulation. Review the versions, origins, disk use and proposed dependency changes. Then explicitly apply:

```sh
sudo bash deploy/setup-device.sh --display-backend wayland --apply
/usr/bin/python3 deploy/preflight.py --display-backend wayland \
  --require-pi --require-software \
  --output "$HOME/thirsty-preflight-$(date +%Y%m%d-%H%M%S).json"
```

Apt asks for confirmation. The script neither enables the kiosk nor configures GPIO. Use a new preflight filename each time; archive evidence privately. Run as the non-root maintenance user, not root. Success establishes package eligibility, **not** graphics or electrical acceptance. This walkthrough explicitly selects packaged Weston/Wayland; missing EGLFS is not a reason to build Qt on a 512 MB board.

## 4. Establish the actual display and mock trial

Use a **local active VT login**, normally VT1, with no competing desktop/compositor. SSH alone cannot establish DRM master or an active seat. Check `loginctl session-status`, actual `/dev/dri/` and `/dev/input/` ownership, and your groups. Resolve image/logind permissions as described in [device setup](device.md#display-route-seat-and-permissions); never run Weston/Qt as root or `chmod 666` device nodes.

From that local non-root login, record:

```sh
id
loginctl session-status
printf 'Runtime: %s\n' "$XDG_RUNTIME_DIR"
stat -c '%U %a %n' "$XDG_RUNTIME_DIR"
ls -l /dev/dri/
```

The PAM/logind runtime directory must exist, belong to this user and be private (0700). If missing, repair the local login/session rather than creating a shared `/tmp` runtime.

First discover the **actual Weston connector, DRM card and GL renderer**. A discovery-only launch from the local VT may use the monitor's default mode; this is not the 720p acceptance trial:

```sh
weston --backend=drm --renderer=gl --shell=kiosk-shell.so \
  --idle-time=0 --socket=thirsty-wayland --no-config \
  --log="$HOME/thirsty-weston-discovery.log"
```

Inspect its log from a same-user SSH session. Stop it with Ctrl+C at its launching console when accessible, or identify its actual PID from that user's process list and send `kill -TERM` to that PID from SSH. Do not kill guessed processes. Record Weston-reported connector/card and supported modes. If it cannot start or uses software rendering, stop and diagnose; no root or pixman fallback.

Create `~/.config/weston.ini` using `mkdir -p ~/.config` and an editor. Replace the two marked values with the **observed connector** and **actual XKB layout**; do not run with these placeholder words:

```ini
[core]
shell=kiosk-shell.so
idle-time=0
xwayland=false
require-input=false

[output]
name=OBSERVED_WESTON_CONNECTOR
mode=1280x720
scale=1

[keyboard]
keymap_layout=ACTUAL_XKB_LAYOUT
```

Add a keyboard variant only if required by your keyboard. If the screen does not support 1280×720, resolve that explicitly; do not call a differently sized mode a pass. Launch again on the local VT:

```sh
weston --backend=drm --renderer=gl --shell=kiosk-shell.so \
  --idle-time=0 --socket=thirsty-wayland --config="$HOME/.config/weston.ini" \
  --log="$HOME/thirsty-weston-trial.log"
```

Wait until the log reports compositor readiness. In **SSH as the exact same user**, set `XDG_RUNTIME_DIR` to the path printed in that user's local session, verify ownership/mode again, and check that its socket exists:

```sh
read -r -p 'Paste the local session runtime path: ' XDG_RUNTIME_DIR
export XDG_RUNTIME_DIR
stat -c '%U %a %n' "$XDG_RUNTIME_DIR"
test -S "$XDG_RUNTIME_DIR/thirsty-wayland"
cd /opt/thirsty
env -u DISPLAY -u QT_QPA_EGLFS_INTEGRATION -u QT_QPA_EGLFS_KMS_CONFIG \
  PYTHONDONTWRITEBYTECODE=1 QML_DISABLE_DISK_CACHE=1 \
  WAYLAND_DISPLAY=thirsty-wayland QT_QPA_PLATFORM=wayland QSG_RHI_BACKEND=opengl \
  /usr/bin/python3 -m app --mode mock \
  --device /opt/thirsty/config/device.json \
  --script /opt/thirsty/config/script.json --fullscreen
```

Do not proceed if the socket/session checks fail. **`python3 -m app` is the public entry point**, not `python3 -m app.main`. Qt runs in the SSH foreground, while Weston still owns the active local VT. Ctrl+C in SSH stops the app; then stop Weston separately. Never start a second app/compositor while a service owns the seat.

Verify actual HDMI 1280×720 scanout in Weston/monitor evidence, hardware GL (not llvmpipe), fonts, all SVGs, QR and synthetic typing. Disable the monitor's own sleep; trial prolonged idle. Window dimensions alone prove none of these.

Before approving service permissions, repeat the local display trial as the dedicated `thirsty` identity. For a fresh image you may temporarily create it as follows, **only after confirming these image groups exist**:

```sh
getent group video render input
sudo useradd --system --user-group --create-home --home-dir /var/lib/thirsty \
  --shell /bin/bash --groups video,render,input thirsty
sudo passwd thirsty
```

If `thirsty` already exists, inspect it and follow the [dedicated-account contract](../deploy/systemd/README.md#prerequisites-and-approval-record); do not repurpose a maintenance account. Log in locally as `thirsty`, create its reviewed Weston config, repeat the mock trial and non-root preflight. A second same-user local shell or authorized same-user SSH session can launch Qt using the verified runtime; do not weaken SSH policy merely for this trial. No `gpio` group is needed for mock. After testing, stop both processes, log out every temporary `thirsty` session, and from the maintenance account:

```sh
sudo usermod --shell /usr/sbin/nologin thirsty
sudo passwd --lock thirsty
```

Remove temporary trial SSH authorization if one was added. Never grant this account sudo. The installer will constrain it for the service.

## 5. Approval, service installation and supervised mock trial

Create a private evidence directory and operator-authored files:

```sh
sudo install -d -m 0700 /root/thirsty-maintenance
sudoedit /root/thirsty-maintenance/approval.json
sudoedit /root/thirsty-maintenance/weston.ini
```

Use your tested Weston INI. The approval JSON must contain `backend` (`"wayland"`), `drm_card` (actual `/dev/dri/cardN`), `connector` (exact Weston name), `keyboard_layout`, and `record` (reference to dated private evidence). It also requires `graphics_verified`, `seat_verified`, `permissions_verified`, `blanking_verified`: set each true **only after actually verifying it**. There is deliberately no copy-paste “all approved” JSON here. If evidence is missing, remain at manual mock trials. See the [full approval schema and display requirements](../deploy/systemd/README.md#prerequisites-and-approval-record).

Keep VT1 for recovery. Reserve VT7 for the service: inspect `systemctl status getty@tty7.service` and `loginctl`; remove any actual competing VT7 login/getty deliberately and record its prior state. Do not mask random gettys or leave another shell reading visitor keystrokes. Stop all manual display trials first.

Plan, then install **mock without boot enablement**:

```sh
cd /opt/thirsty
sudo /usr/bin/python3 deploy/systemd/install.py --display-backend wayland --mode mock \
  --approval /root/thirsty-maintenance/approval.json \
  --display-config /root/thirsty-maintenance/weston.ini
sudo /usr/bin/python3 deploy/systemd/install.py --display-backend wayland --mode mock \
  --approval /root/thirsty-maintenance/approval.json \
  --display-config /root/thirsty-maintenance/weston.ini --apply
artwork start
systemctl status thirsty.service
sudo journalctl --namespace=thirsty -u thirsty.service --since today
loginctl list-sessions
```

Inspect the actual kiosk session with `loginctl session-status` followed by its observed session ID: it must be `thirsty`, active seat0, VT7. The helper creates `/run/thirsty` for both Weston and Qt; do not substitute your maintenance runtime. Test typing, blanking, keyboard absence/reconnection and the recovery cases in the [service runbook](../deploy/systemd/README.md#safe-planning-and-explicit-install). Stop with:

```sh
sudo systemctl stop thirsty.service
```

The installer does not start the service; `--apply` without `--enable` leaves it disabled. Mock trials are not a live exhibition. Leave boot disabled while commissioning.

**Everyday startup:** `artwork start` works from any directory, including over SSH, and asks for your maintenance user's sudo authorization when needed. The installer places it at `/usr/local/bin/artwork`; if your shell omits `/usr/local/bin` from `PATH`, use `/usr/local/bin/artwork start`. It starts the installed `thirsty.service`, retaining its non-root kiosk user, approved backend/mode, VT7/PAM session and restart policy. It does not launch Qt in your SSH session, choose mock/live, enable boot, or bypass approval. Starting an already running service does not reset the visitor journey. Check `systemctl status thirsty.service` and the journal above: a successful start request is not proof that graphics or hardware passed.

**Existing Pi update:** stop with `sudo systemctl stop thirsty.service`, update the reviewed root-owned `/opt/thirsty` checkout (preserving your commissioned device config and private approval/display files), then rerun the full installer command above with `--apply`. This installs/updates the command as well as the service helpers; no pip install or virtualenv is needed. Use your previously approved backend, display-config path and mode, not `mock` if the installation is already commissioned for live operation. Include `--enable` only if you intend to retain approved boot startup; omitting it disables boot startup. Then run `artwork start`. Merely updating the checkout or rerunning `deploy/setup-device.sh` does not install this command.

## 6. Your four sensors: recorded map, installation-specific approval

The operator-tested low-to-high mapping is:

| Switch | Position | Cable color | BCM GPIO | Physical header pin |
| --- | --- | --- | ---: | ---: |
| S1 / index 0 | Lowest | Lila/Weiß | 27 | 13 |
| S2 / index 1 | Second | Gelb | 22 | 15 |
| S3 / index 2 | Third | Blau | 23 | 16 |
| S4 / index 3 | Highest | Grün | 24 | 18 |

The shared supply is assigned to **3.3 V on physical pin 1**. The operator reported raw dry `1` and wet `0` for all four switches; use `wet_values: [0, 0, 0, 0]`. Successful live operation was reported on 2026-11-20; see the [installation record](operator.md). Repository backend/approval defaults remain null/false intentionally. Do not run live mode on a new installation before commissioning: populated GPIO numbers alone allow the direct app CLI to attempt input initialization; the deployment approval flags are enforced separately by the service gate.

These are distinct numbering systems. Confirm pin-1 orientation, cable labels, actual switch order and enabled-interface conflicts before wiring a new installation. Preserve your commissioned four-element configuration during updates; do not overwrite it with repository approval defaults or a two-sensor example.

**First verify the exact sensor model and electrical behavior.** A powered sensor/module is not interchangeable with a passive contact. If it needs power or exposes a voltage output, stop: its datasheet, measured output and suitable 3.3 V interface must be reviewed before connecting it. Do not assume “JO-GL534” or a printed voltage/current rating establishes passive isolation.

Only after disconnected, isolated continuity tests prove suitable passive two-wire contacts is the project's topology applicable: **Pi 3.3 V → passive contact → GPIO**, with `pull_up=False`. Physical pins 1/17 are 3.3 V; 2/4 are **5 V and must never feed GPIO**. Power down and disconnect all supplies before wiring. Verify rails/harness isolation, keep water away from powered electronics, and never use live jumper shorts to simulate water.

Follow [operator §2 electrical safety](operator.md#2-electrical-and-water-safety--before-connecting-gpio) and [§3 supervised input commissioning](operator.md#3-supervised-input-commissioning-and-configuration) exactly, including its bounded input-only diagnostic, private `LG_WD`, non-root chip permissions and safe cleanup. Record dry/wet raw bits for **each** switch: wet need not mean closed or raw 1. Do not invent `wet_values`, set `hardware_verified=true`, or select `pin_factory="lgpio"` just to get past a gate. Keep the backend unresolved and hardware assertion false until that commissioning provides evidence. Package availability is not backend verification.

After commissioning, edit only the measured device configuration with `sudoedit /opt/thirsty/config/device.json`, preserve root ownership and repeat the full gate. Stop service/diagnostics before editing or changing wiring. Any wiring/orientation/backend change revokes the affected approval.

## 7. Live trial, acceptance, then explicit boot enablement

Only after electrical/backend/polarity commissioning and real display approval, install live **without enabling boot**:

```sh
cd /opt/thirsty
sudo /usr/bin/python3 deploy/systemd/install.py --display-backend wayland --mode live \
  --approval /root/thirsty-maintenance/approval.json \
  --display-config /root/thirsty-maintenance/weston.ini --apply
sudo systemctl start thirsty.service
systemctl status thirsty.service
sudo journalctl --namespace=thirsty -u thirsty.service --since today
```

Complete [operator §4](operator.md#4-fill-drain-refill-and-tune) and its remaining acceptance checklist: five levels, safe invalid-pattern checks, empty pause, refill hold/resume, timing, at least three physical drain/refill cycles, eight-hour run, reset/recovery, actual kiosk-user GPIO access, keyboard reconnect, owner copy approval and phone QR scan. Mock results do not substitute for physical water tests.

**512 MB acceptance is still open.** During synthetic Start/typing/scrolling/reset runs, use preflight `--pid` with the observed app PID and separately the Weston PID; retain new dated reports. Observe `free -h`, `vmstat 1`, `swapon --show`, maintenance kernel OOM logs and `vcgencmd get_throttled` over time. Record supply/throttling, responsiveness and sustained swap behavior. No workstation pass proves arm64 RAM headroom; OOM, sustained thrashing or software rendering blocks unattended deployment.

Only after the complete physical/service acceptance record is signed off, stop the trial and repeat the **full** installer selection with explicit boot authorization:

```sh
sudo systemctl stop thirsty.service
cd /opt/thirsty
sudo /usr/bin/python3 deploy/systemd/install.py --display-backend wayland --mode live \
  --approval /root/thirsty-maintenance/approval.json \
  --display-config /root/thirsty-maintenance/weston.ini --apply --enable
sudo systemctl start thirsty.service
```

`--enable` does not start it immediately. Then perform a supervised reboot and verify offline cold boot and recovery. If acceptance fails, `sudo systemctl disable --now thirsty.service` returns to maintenance; use the [rollback procedure](../deploy/systemd/README.md#stop-and-rollback), preserving your evidence/config. Do not bypass failure by changing only an environment variable or silently falling back to mock.

## 8. Bluetooth and focused troubleshooting

Pair during maintenance, with a recovery keyboard/console available:

```sh
sudo systemctl enable --now bluetooth.service
sudo rfkill unblock bluetooth
bluetoothctl
```

Inside `bluetoothctl`: `power on`, `agent KeyboardDisplay`, `default-agent`, `scan on`. Identify the actual keyboard, then use `pair`, `trust`, `connect`, and `info`, each with its observed device identifier; follow the displayed passkey instructions on the real keyboard. Finish with `scan off`, `discoverable off`, `quit`. Do not copy a sample MAC. Test layout/punctuation, sleep/wake, keyboard power cycle, Pi reboot and keyboard absent at boot then reconnecting.

Only when local recovery is ready, Wi-Fi can be disabled with `sudo rfkill block wifi`; **this disconnects Wi-Fi SSH**. Do not block all radios or disable Bluetooth. Verify the intended radio policy after reboot; the app itself needs no network, while the QR destination is accessed by a visitor's phone.

| Symptom | Next action |
| --- | --- |
| PySide6 package absent | Check `dpkg --print-architecture`, Trixie image and official apt sources/update output. armhf requires reflash, not a Debian repository graft or pip. |
| Weston cannot open DRM / seat inactive | Return to the active local VT, stop competing display owners, inspect logind and actual node permissions. Do not run as root. |
| Qt cannot connect to Wayland | Verify Weston readiness and exact same user, private runtime and `thirsty-wayland` socket. SSH environment is not inherited from the local session. |
| Wrong HDMI size / llvmpipe | Inspect Weston log, observed connector and monitor modes. Do not approve window size as output mode or accept software rendering. |
| Service refuses config/approval | Read the namespaced journal and gate error. Supply measured evidence or correct ownership/config; never flip verification flags merely to pass. |
| Start limit reached | Stop, diagnose the namespaced journal, fix cause, then `sudo systemctl reset-failed thirsty.service` and retry under supervision. |
| GPIO failure / inconsistent levels | Stop live mode; recheck the operator electrical/calibration procedure and non-root access. Never raise voltage, relax node permissions globally or hide faults with longer filters. |
| OOM, lag or power warning | Stop acceptance; record app/compositor memory, sustained swap and power/throttling evidence on the actual Pi. Do not claim the 512 MB deployment is proven. |

For normal shutdown: stop the kiosk, run `sudo poweroff`, wait for shutdown, then remove power. Keep a verified recoverable card backup and an independent maintenance path before unattended operation.
