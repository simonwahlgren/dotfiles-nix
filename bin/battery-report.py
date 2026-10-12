#!/usr/bin/env python3
"""Sample Linux battery drain and CPU activity; save text and JSON reports."""

import argparse
from collections import defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def number(path):
    try:
        return int(read(path))
    except (TypeError, ValueError):
        return None


def battery_snapshot():
    batteries, external = {}, {}
    for path in Path('/sys/class/power_supply').glob('*'):
        if read(path / 'scope') == 'Device':
            continue
        if read(path / 'type') != 'Battery':
            online = number(path / 'online')
            if online is not None:
                external[path.name] = online
            continue
        if number(path / 'present') == 0:
            continue
        power = number(path / 'power_now')
        if power is None:
            current = number(path / 'current_now')
            voltage = number(path / 'voltage_now')
            if current is not None and voltage is not None:
                power = abs(current * voltage) / 1_000_000
        batteries[path.name] = {
            'status': read(path / 'status'),
            'watts': abs(power) / 1_000_000 if power is not None else None,
            'capacity_percent': number(path / 'capacity'),
        }
    valid = (bool(batteries) and not any(external.values()) and all(
        b['status'] == 'Discharging' and b['watts'] is not None
        for b in batteries.values()
    ))
    return {
        'batteries': batteries,
        'external_power': external,
        'discharge_watts': sum(b['watts'] for b in batteries.values()) if valid else None,
    }


def processes():
    result = {}
    for path in Path('/proc').glob('[0-9]*/stat'):
        raw = read(path)
        if not raw:
            continue
        try:
            left, right = raw.index('('), raw.rindex(')')
            fields = raw[right + 2:].split()
            key = (int(path.parent.name), int(fields[19]))
            result[key] = (raw[left + 1:right], int(fields[11]) + int(fields[12]))
        except (ValueError, IndexError):
            continue
    return result


def settings():
    brightness = {}
    for path in Path('/sys/class/backlight').glob('*'):
        current, maximum = number(path / 'actual_brightness'), number(path / 'max_brightness')
        brightness[path.name] = round(100 * current / maximum, 1) if current is not None and maximum else None
    gpus = {}
    for path in Path('/sys/bus/pci/devices').glob('*'):
        device_class = read(path / 'class')
        if device_class and device_class.startswith('0x03'):
            gpus[path.name] = {field: read(path / field) for field in (
                'vendor', 'device', 'power/runtime_status', 'power/control',
            )}
    policies = list(Path('/sys/devices/system/cpu/cpufreq').glob('policy*'))
    return {
        'platform_profile': read('/sys/firmware/acpi/platform_profile'),
        'cpu_governors': sorted({v for p in policies if (v := read(p / 'scaling_governor'))}),
        'cpu_energy_preferences': sorted({v for p in policies if (v := read(p / 'energy_performance_preference'))}),
        'brightness_percent': brightness,
        'gpus': gpus,
    }


def positive(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError('must be a finite positive number')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        'Unplug AC and use the laptop normally. Compare runs with the same workload, '
        'changing one setting at a time. No power settings are changed.'
    ))
    parser.add_argument('--seconds', type=positive, default=60, help='sampling duration (default: 60)')
    parser.add_argument('--interval', type=positive, default=2, help='sampling interval (default: 2 seconds)')
    parser.add_argument('--output', type=Path, help='new report directory (default: timestamped directory here)')
    parser.add_argument('--powertop', action='store_true', help='also run a separate PowerTOP HTML capture; requires root and adds --seconds to runtime')
    args = parser.parse_args()
    if args.powertop and (os.geteuid() != 0 or not shutil.which('powertop')):
        parser.error('--powertop requires root and powertop on PATH')
    output = args.output or Path('battery-report-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    output.mkdir(parents=True, exist_ok=False)
    initial_settings = settings()
    previous = processes()
    totals = defaultdict(int)
    names = {}
    start = time.monotonic()
    samples = [dict(elapsed_seconds=0, **battery_snapshot())]
    print(f'Sampling for {args.seconds:g} seconds. Reports: {output.resolve()}', flush=True)
    if samples[0]['discharge_watts'] is None:
        print('Battery is not discharging or its power sensor is unavailable; CPU activity will still be measured.', flush=True)
    while time.monotonic() - start < args.seconds:
        time.sleep(min(args.interval, max(0, args.seconds - (time.monotonic() - start))))
        current = processes()
        for key, (name, ticks) in current.items():
            if key in previous:
                totals[key] += max(0, ticks - previous[key][1])
                names[key] = name
        previous = current
        sample = battery_snapshot()
        samples.append(dict(elapsed_seconds=time.monotonic() - start, **sample))
    elapsed = samples[-1]['elapsed_seconds']
    hz = os.sysconf('SC_CLK_TCK')
    ranked = [
        {'pid': key[0], 'name': names[key], 'cpu_percent': round(ticks / hz / elapsed * 100, 2)}
        for key, ticks in sorted(totals.items(), key=lambda item: item[1], reverse=True) if ticks
    ]
    watt_seconds = valid_seconds = 0
    for before, after in zip(samples, samples[1:]):
        a, b = before['discharge_watts'], after['discharge_watts']
        if a is not None and b is not None and before['batteries'].keys() == after['batteries'].keys():
            duration = after['elapsed_seconds'] - before['elapsed_seconds']
            watt_seconds += (a + b) / 2 * duration
            valid_seconds += duration
    average = watt_seconds / valid_seconds if valid_seconds else None
    report = {
        'created_at': datetime.now().astimezone().isoformat(),
        'duration_seconds': elapsed,
        'valid_discharge_seconds': valid_seconds,
        'average_discharge_watts': average,
        'processes': ranked,
        'settings_start': initial_settings,
        'settings_end': settings(),
        'samples': samples,
    }
    lines = [f'Battery report — {elapsed:.1f} seconds']
    if average is None:
        lines.append('Battery drain: unavailable (requires discharging battery and a power sensor).')
    else:
        lines.append(f'Average battery drain: {average:.2f} W over {valid_seconds:.1f} valid seconds.')
    lines += [
        '', 'Top processes by CPU activity (100% = one CPU core):',
        f'{"PID":>7} {"CPU %":>8}  NAME',
        *[f'{p["pid"]:7} {p["cpu_percent"]:8.2f}  {p["name"]}' for p in ranked[:20]],
        '', 'CPU activity is a clue, not per-process watts. GPU, display and device power are not attributed.',
        'Processes that exit between samples may be missed; process names may be truncated.',
        '', 'Settings at end of sample:',
        json.dumps(report['settings_end'], indent=2),
        '', 'Compare unplugged runs with the same workload. Change one setting or close one app per run.',
        'For power-saving experiments, check the busiest apps, brightness, and any active discrete GPU.',
        'An active GPU alone does not establish its power draw.',
    ]
    if initial_settings != report['settings_end']:
        lines.append('Settings changed during sampling; both snapshots are in report.json.')
    if args.powertop:
        print('Capturing PowerTOP in a separate measurement interval...', flush=True)
        with (output / 'powertop.log').open('w') as log:
            try:
                result = subprocess.run(
                    ['powertop', f'--time={max(1, math.ceil(args.seconds))}', f'--html={output.resolve() / "powertop.html"}'],
                    stdout=log, stderr=subprocess.STDOUT, timeout=args.seconds + 60,
                )
                report['powertop_returncode'] = result.returncode
                success = result.returncode == 0 and (output / 'powertop.html').is_file()
                lines.append('PowerTOP: see powertop.html (separate interval; power estimates may be unavailable).' if success else 'PowerTOP failed; see powertop.log.')
            except (OSError, subprocess.TimeoutExpired) as error:
                report['powertop_error'] = str(error)
                lines.append(f'PowerTOP failed: {error}; see powertop.log.')
    text = '\n'.join(lines) + '\n'
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'report.txt').write_text(text)
    print(text, end='')
    print(f'Saved to {output.resolve()}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit('\nCancelled.')
    except OSError as error:
        raise SystemExit(str(error))
