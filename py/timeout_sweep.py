#!/usr/bin/env python3
"""Sweep asymmetric DM timeouts: rebuild, flash, measure success rate over serial."""

import argparse
import json
import os
import subprocess
import sys
import time

import serial

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def measure(com: str, count: int, settle_s: float) -> dict:
    time.sleep(settle_s)
    ok = timed_out = other = 0
    durations = []
    distances = []

    with serial.Serial(com, baudrate=115200, timeout=10) as ser:
        for _ in range(count):
            ser.write(b"0")
            raw = ser.read_until(b"\n")
            try:
                obj = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                other += 1
                continue

            if obj.get("timed_out", 0):
                timed_out += 1
                continue

            sinr_r = sum(obj.get("sinr_remote", []))
            sinr_l = sum(obj.get("sinr_local", []))
            quality = obj.get("quality", 100)

            if quality == 0 and sinr_r < 5 and sinr_l < 5:
                ok += 1
                durations.append(obj.get("duration[us]", -1))
                distances.append(obj.get("ifft[mm]", 0) / 1000.0)
            else:
                other += 1

            time.sleep(0.1)

    dist_std = 0.0
    if len(distances) > 1:
        mean = sum(distances) / len(distances)
        dist_std = (sum((d - mean) ** 2 for d in distances) / len(distances)) ** 0.5

    return {
        "ok": ok,
        "timed_out": timed_out,
        "other": other,
        "count": count,
        "success_rate": ok / count if count else 0.0,
        "duration_us_max": max(durations) if durations else -1,
        "distance_std_m": dist_std,
    }


def build_flash(init_us: int, refl_us: int, skip_flash: bool) -> None:
    env = os.environ.copy()
    subprocess.run(
        [
            "make",
            "-C",
            ROOT,
            "build",
            f"INITIATOR_TIMEOUT_US={init_us}",
            f"REFLECTOR_TIMEOUT_US={refl_us}",
        ],
        check=True,
        env=env,
    )
    if skip_flash:
        return
    subprocess.run(["make", "-C", ROOT, "flashr"], check=True, env=env)
    subprocess.run(["make", "-C", ROOT, "flashi"], check=True, env=env)


def pick_best(results: list) -> dict:
    return max(results, key=lambda r: (r["success_rate"], -r["initiator_us"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--com",
        default="/dev/tty.usbmodem0006857014091",
        help="Initiator serial port",
    )
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument(
        "--initiator-timeouts",
        default="40000,50000,60000",
        help="Comma-separated initiator timeout values (microseconds)",
    )
    parser.add_argument(
        "--reflector-timeouts",
        default="200000,500000,1000000",
        help="Comma-separated reflector timeout values (microseconds)",
    )
    parser.add_argument("--settle", type=float, default=2.0, help="Seconds after flash")
    parser.add_argument("--skip-flash", action="store_true")
    args = parser.parse_args()

    init_timeouts = [int(x.strip()) for x in args.initiator_timeouts.split(",") if x.strip()]
    refl_timeouts = [int(x.strip()) for x in args.reflector_timeouts.split(",") if x.strip()]
    results = []

    print(
        f"Sweeping {len(init_timeouts)}x{len(refl_timeouts)} asymmetric pairs, "
        f"{args.count} samples each\n"
    )
    for init_us in init_timeouts:
        for refl_us in refl_timeouts:
            if refl_us < init_us:
                continue
            print(f"=== initiator={init_us} us  reflector={refl_us} us ===")
            build_flash(init_us, refl_us, args.skip_flash)
            stats = measure(args.com, args.count, args.settle)
            row = {"initiator_us": init_us, "reflector_us": refl_us, **stats}
            results.append(row)
            print(
                f"  ok={stats['ok']}/{stats['count']} "
                f"timed_out={stats['timed_out']} other={stats['other']} "
                f"success={stats['success_rate']*100:.0f}% "
                f"dur_max={stats['duration_us_max']}us\n"
            )

    best = pick_best(results)
    print("--- summary ---")
    for r in sorted(results, key=lambda x: -x["success_rate"]):
        mark = ""
        if (
            r["initiator_us"] == best["initiator_us"]
            and r["reflector_us"] == best["reflector_us"]
        ):
            mark = " <-- recommended"
        print(
            f"  init={r['initiator_us']:6d} refl={r['reflector_us']:7d} us: "
            f"{r['success_rate']*100:5.1f}% ok, {r['timed_out']} timeouts{mark}"
        )
    print(
        f"\nRecommended:\n"
        f"  make build flashr flashi "
        f"INITIATOR_TIMEOUT_US={best['initiator_us']} "
        f"REFLECTOR_TIMEOUT_US={best['reflector_us']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
