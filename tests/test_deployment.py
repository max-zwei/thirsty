"""Portable deployment regressions; no GPIO, compositor or systemd is started."""
import importlib.util
from pathlib import Path
import signal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def deployment(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'deploy/systemd'))
    modules = {}
    for name in ('run', 'install', 'artwork'):
        spec = importlib.util.spec_from_file_location(
            'deployment_' + name, ROOT / 'deploy/systemd' / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name] = module
    return SimpleNamespace(**modules)


@pytest.mark.parametrize('uid', [0, 1000])
def test_artwork_start_uses_installed_service_from_any_directory(deployment, monkeypatch, tmp_path, uid):
    artwork = deployment.artwork
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(artwork.sys, 'argv', ['artwork', 'start'])
    monkeypatch.setattr(artwork.os, 'geteuid', lambda: uid)
    execute = Mock()
    monkeypatch.setattr(artwork.os, 'execv', execute)
    artwork.main()
    command = ['/usr/bin/systemctl', 'start', 'thirsty.service']
    if uid:
        command = ['/usr/bin/sudo', '--', *command]
    execute.assert_called_once_with(command[0], command)


@pytest.mark.parametrize('arguments', [[], ['restart'], ['start', '--mode', 'live'], ['--help']])
def test_artwork_invalid_arguments_and_help_do_not_start(deployment, monkeypatch, arguments):
    artwork = deployment.artwork
    monkeypatch.setattr(artwork.sys, 'argv', ['artwork', *arguments])
    execute = Mock()
    monkeypatch.setattr(artwork.os, 'execv', execute)
    with pytest.raises(SystemExit) as result:
        artwork.main()
    assert result.value.code == (0 if arguments == ['--help'] else 2)
    execute.assert_not_called()


def test_installed_command_is_root_owned_and_executable(deployment, monkeypatch, tmp_path):
    destination = tmp_path / 'bin' / 'artwork'
    ownership = Mock()
    monkeypatch.setattr(deployment.install.os, 'chown', ownership)
    deployment.install.install(ROOT / 'deploy/systemd/artwork.py', destination, mode=0o755)
    ownership.assert_called_once_with(destination, 0, 0)
    assert destination.stat().st_mode & 0o777 == 0o755
    assert destination.read_bytes() == (ROOT / 'deploy/systemd/artwork.py').read_bytes()


@pytest.mark.parametrize('parent_alive', [True, False])
def test_parent_death_is_armed_before_identity_check(deployment, monkeypatch, parent_alive):
    run = deployment.run
    events = []
    prctl = Mock(side_effect=lambda *args: events.append(('prctl', args)) or 0)
    monkeypatch.setattr(run.ctypes, 'CDLL', lambda *a, **kw: SimpleNamespace(prctl=prctl))
    monkeypatch.setattr(run.os, 'getppid', lambda: events.append(('parent',)) or (123 if parent_alive else 1))
    monkeypatch.setattr(run.os, 'getpid', lambda: 456)
    monkeypatch.setattr(run.os, 'kill', lambda *args: events.append(('kill', args)))
    monkeypatch.setattr(run.os, '_exit', Mock(side_effect=SystemExit(1)))
    monkeypatch.setattr(run.os, 'execvpe', lambda *args: events.append(('exec', args)))
    if parent_alive:
        run.exec_child(123, ['/bin/target', '--flag'])
        assert events[2][0] == 'exec'
        assert events[2][1][:2] == ('/bin/target', ['/bin/target', '--flag'])
    else:
        with pytest.raises(SystemExit):
            run.exec_child(123, ['/bin/target'])
        assert events[2] == ('kill', (456, signal.SIGKILL))
        assert not any(event[0] == 'exec' for event in events)
    assert events[:2] == [('prctl', (1, signal.SIGKILL, 0, 0, 0)), ('parent',)]


def test_parent_death_setup_failure_never_executes(deployment, monkeypatch):
    run = deployment.run
    monkeypatch.setattr(run.ctypes, 'CDLL', lambda *a, **kw: SimpleNamespace(prctl=Mock(return_value=-1)))
    monkeypatch.setattr(run.ctypes, 'get_errno', lambda: 1)
    execute = Mock()
    monkeypatch.setattr(run.os, 'execvpe', execute)
    with pytest.raises(OSError):
        run.exec_child(123, ['/bin/target'])
    execute.assert_not_called()


@pytest.mark.parametrize('bad_kind', ['owner', 'writable', 'symlink'])
@pytest.mark.parametrize('bad_index', range(4))
def test_immutable_gate_rejects_ancestors_tree_and_links(deployment, monkeypatch, bad_kind, bad_index):
    visited = []

    class Node:
        def __init__(self, index):
            self.index = index

        def lstat(self):
            visited.append(self.index)
            bad = self.index == bad_index
            return SimpleNamespace(st_uid=1000 if bad and bad_kind == 'owner' else 0,
                                   st_mode=0o777 if bad and bad_kind == 'writable' else 0o755)

        def is_symlink(self):
            return self.index == bad_index and bad_kind == 'symlink'

    root, opt, app, child = [Node(i) for i in range(4)]
    app.parents = (opt, root)
    app.rglob = lambda pattern: iter((child,))
    monkeypatch.setattr(deployment.install, 'APP', app)
    with pytest.raises(ValueError):
        deployment.install.require_immutable_app()
    assert visited == list(range(bad_index + 1))


@pytest.mark.parametrize('require_input', [None, 'true', 'false'])
def test_weston_requires_keyboard_independent_startup(deployment, monkeypatch, tmp_path, require_input):
    import gate
    import json
    monkeypatch.setattr(gate, 'APP', ROOT)
    monkeypatch.setattr(Path, 'is_char_device', lambda self: True)
    preflight = Mock()
    monkeypatch.setattr(gate.subprocess, 'run', preflight)
    approval = tmp_path / 'approval.json'
    approval.write_text(json.dumps({
        'backend': 'wayland', 'graphics_verified': True, 'seat_verified': True,
        'permissions_verified': True, 'blanking_verified': True,
        'record': 'synthetic test only', 'connector': 'TEST-1', 'keyboard_layout': 'us',
        'drm_card': '/dev/dri/card0',
    }))
    display = tmp_path / 'weston.ini'
    display.write_text(
        '[core]\nshell=kiosk-shell.so\nidle-time=0\nxwayland=false\n'
        + ('' if require_input is None else f'require-input={require_input}\n')
        + '[output]\nname=TEST-1\nmode=1280x720\nscale=1\n'
        '[keyboard]\nkeymap_layout=us\n')
    if require_input == 'false':
        gate.validate(approval, 'wayland', 'mock', display)
        preflight.assert_called_once()
    else:
        with pytest.raises(ValueError, match=r'core.require-input=false'):
            gate.validate(approval, 'wayland', 'mock', display)
        preflight.assert_not_called()


@pytest.fixture
def preflight(monkeypatch):
    spec = importlib.util.spec_from_file_location('deployment_preflight', ROOT / 'deploy/preflight.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # All inventory boundaries are synthetic: no device files, commands, Qt or GPIO.
    host = SimpleNamespace(
        architecture='arm64', python_bytes=8, system='Linux', codename='trixie',
        model='Raspberry Pi 3 Model A Plus Rev 1.0')
    monkeypatch.setattr(module, 'text_file', lambda path: {
        'status': 'ok', 'value': {
            '/proc/device-tree/model': host.model,
            '/etc/os-release': f'ID=debian\nVERSION_CODENAME={host.codename}\n',
        }.get(str(path), ''),
    })
    monkeypatch.setattr(module, 'command', lambda argv: {
        'status': 'ok', 'stdout': host.architecture if argv == ['dpkg', '--print-architecture'] else '',
    })
    monkeypatch.setattr(module, 'struct', SimpleNamespace(calcsize=lambda fmt: host.python_bytes))
    monkeypatch.setattr(module, 'platform', SimpleNamespace(
        system=lambda: host.system, release=lambda: 'synthetic',
        machine=lambda: 'aarch64', python_version=lambda: '3.13.0'))
    monkeypatch.setattr(module, 'qt_inventory', lambda: {})
    monkeypatch.setattr(module, 'module_info', lambda *args: {
        'available': False, 'distribution_version': None})
    monkeypatch.setattr(module, 'package_inventory', lambda backend: {'missing': ['python3-pyside6.qtcore']})
    monkeypatch.setattr(module, 'sensor_config', lambda path: {'live_configuration_complete': False})
    monkeypatch.setattr(module, 'device_nodes', lambda: [])
    monkeypatch.setattr(module, 'process_memory', lambda pid: {})
    monkeypatch.setattr(Path, 'glob', lambda *args: iter(()))
    monkeypatch.setattr(module.os, 'getgroups', lambda: [])
    monkeypatch.setattr(module.os, 'geteuid', lambda: 1000)
    monkeypatch.delenv('XDG_SESSION_ID', raising=False)
    return module, host


@pytest.mark.parametrize('overrides,eligible', [
    ({}, True),
    ({'architecture': 'armhf', 'python_bytes': 4}, False),
    ({'architecture': 'armhf', 'python_bytes': 8}, False),
    ({'architecture': 'arm64', 'python_bytes': 4}, False),
    ({'architecture': 'amd64'}, False),
    ({'model': 'Raspberry Pi 3 Model B Plus Rev 1.3'}, False),
    ({'system': 'Darwin'}, False),
    ({'codename': 'bookworm'}, False),
])
def test_preflight_target_gate(preflight, monkeypatch, capsys, overrides, eligible):
    import json
    module, host = preflight
    for name, value in overrides.items():
        setattr(host, name, value)
    monkeypatch.setattr(module.sys, 'argv', ['preflight.py', '--require-pi'])
    assert module.main() == (0 if eligible else 2)
    report = json.loads(capsys.readouterr().out)
    assert report['schema_version'] == 2
    eligibility = report['eligibility']
    assert eligibility['target_eligible'] is eligible
    assert eligibility['arm64_userspace'] is (host.architecture == 'arm64' and host.python_bytes == 8)
    assert 'armhf_userspace' not in eligibility
    assert report['host']['python_bits'] == host.python_bytes * 8
    assert eligibility['software_baseline_eligible'] is False
    assert eligibility['physical_acceptance_verified'] is False
    assert report['sensors']['live_configuration_complete'] is False


def test_arm64_target_does_not_bypass_software_gate(preflight, monkeypatch, capsys):
    import json
    module, _ = preflight
    monkeypatch.setattr(module.sys, 'argv', ['preflight.py', '--require-pi', '--require-software'])
    assert module.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report['eligibility']['target_eligible'] is True
    assert report['eligibility']['software_baseline_eligible'] is False
    assert report['eligibility']['physical_acceptance_verified'] is False
