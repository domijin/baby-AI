# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repo is currently a **notes / ideation stage** project. There is no source code, no build system, no tests, and no package manifest — only `README.md` (a brain-dump of design ideas) and `LICENSE`. Do not invent build/lint/test commands; there is nothing to run yet. New work will create the first code in the repo, so structural choices (language, layout, tooling) are still open.

## Project intent

The README sketches an AI prototype ("baby-AI") that fuses perception and language on cheap consumer hardware. The pieces it wants to combine:

- **Vision pipeline** — motion tracking + object recognition, with a "smart moment" selector inspired by Google Clips (video → frames → MobileNet-style classifier → motion-flag → keep/discard).
- **Audio pipeline** — ASR to convert speech into an NLP problem; direction-of-arrival from a mic array.
- **Knowledge graph** — links images and words; intended as the persistent "memory" layer.
- **Reinforcement signal** — verbal interaction updates the network. Speculative ideas (spiking nets, random firing, ensembled sub-nets) are noted as research directions, not commitments.

When designing specs or modules, treat these as the four planned subsystems rather than as one monolith.

## Target hardware

Prototype is intended to run across:

- **Yi Dome 1080p camera** (Hi3518EV200, ARM926EJ-S v5l, kernel 3.4.35, gcc 4.8.3) — flashed with [Yi Hack V3](https://github.com/shadow-1/yi-hack-v3). Reachable via SSH (`dropbear`). RTSP is documented as conflicting with the cloud service and is currently not used.
- **ReSpeaker HAT** — audio capture / direction of orientation.
- **Raspberry Pi** — host that aggregates feeds.

Anything ARM-cross-compiled for the Yi Dome must respect the very old toolchain (gcc 4.8.3, kernel 3.4) — assume no modern glibc, no Python 3.10+, no systemd.

## Existing operational workflow (Yi Dome → Pi)

The only working pipeline today is a cron-driven pull of the latest recording from the camera onto the Pi (README lines 55–67). Reproduced here so future sessions don't have to re-derive it:

```bash
HOST='192.168.1.24'

cd ~/Documents
check=`cat latest`
latest=`ssh root@$HOST " cd record ; ls -tr */*.mp4 | tail -1"`
if [ "$check" != "$latest" ]
then
    file=`echo $latest | sed "s/\///g"`
    scp root@$HOST:/tmp/sd/record/$latest Vision/$file
    echo $latest > latest
fi
```

Notes: recordings live under `/tmp/sd/record/` on the camera; `dclient` is not packed on-device, so `scp`/`rsync` initiated *from* the camera doesn't work — the Pi must pull. A `latest` file in `~/Documents` tracks what's already been copied; new files land under `~/Documents/Vision/`.

## Branching

Active development branch is `claude/design-specs-evaluation-UUNNc` (per task instructions). `master` holds the original three commits (initial, task definition, Yi Dome video ingest).
