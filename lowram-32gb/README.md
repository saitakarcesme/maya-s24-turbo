# Maya-S24 on 2× RTX 3090 with only 32 GB of RAM

A replication of [catonooka/maya-s24-turbo](https://github.com/catonooka/maya-s24-turbo) on a rig with the same
GPUs but **1/8 of the RAM**. Engine: [mw00/project-maya](https://github.com/mw00/project-maya) v1.1.20
(`35bb2b2`), model Maya-S24 (94.7 GB, sha256-verified by the setup), 32K context, MTP drafting, vision on.
Measured 2026-10-21.

## The rig, against the reference rig

| | this rig (llmrig) | maya-s24-turbo's rig |
| --- | --- | --- |
| GPUs | 2× RTX 3090 24 GB, no NVLink | 2× RTX 3090 24 GB, no NVLink |
| PCIe | GPU0 4.0 **x16**, GPU1 4.0 **x4** (chipset slot) | both x16 |
| CPU | Core i5-14400F (AVX2, 16 threads) | Threadripper PRO 3955WX |
| RAM | **32 GB** (~24 GB free for Maya) | 247 GB |
| SSD | Kingston NV3 2 TB (DRAM-less) | NVMe |

The difference that matters: their RAM tier pins **55 GB** of experts (`RAM_RESIDENT=1`, 0.00 disk reads/token);
here the RAM tier is **11-16 GB**, so ~25-30 GB of experts are read from the SSD while decoding. GPU1's x4 link
also makes a PCIe expert fetch 1.1 ms there against 0.32 ms on GPU0 (the engine's own CPU-lane line).

## Results

Official bench = `./maya.sh --bench` (greedy, thinking off, 3 answers of 256 tokens; prefill of 2K/8K tokens),
the same bench maya-s24-turbo and project-maya's README report.

| run | settings | decode (3 answers) | prefill 2K | prefill 8K |
| --- | --- | ---: | ---: | ---: |
| A | stock setup | **11.7** (11.2 / 13.2 / 10.5) | 145 | 555 |
| B | maya-s24-turbo's stack minus `RAM_RESIDENT` (`PROMOTE_MIN=6 KV_INT8=1 MTP_KEEP=2 SPEC_SAMPLE=1 SPEC_CANCEL=1`) | **8.0** (8.3 / 10.7 / 5.0) | 24 | 70 |
| C | low-RAM, exact: `DISK_READERS=8 RAM_HEADROOM_GB=4 MTP_KEEP=2 SPEC_SAMPLE=1 SPEC_CANCEL=1` | **12.2** (11.0 / 13.4 / 12.0) | 194 | 657 |
| D | C + `DISK_SKIP_W=0.12` + `MISS_SKIP_W=0.14 MISS_SKIP_FROM=23` (approximate) | **29.1** (25.9 / 30.5 / 30.9) | 197 | 523 |

Production bench = maya-s24-turbo's `v1.1.15-ladder/bench.py` (thinking on, t=0.6; wall clock incl. prefill;
two runs):

| run | run 1 | run 2 | maya-s24-turbo |
| --- | ---: | ---: | ---: |
| C (exact) | 14.9 | 6.2 | |
| D (skip) | **35.2** | **35.7** | 57-59 (v1.1.5), 63.6 (v1.1.15) |

Sustained, D, three answers of 2000 tokens (wall clock): 28.8 / 28.2 / 18.0 tokens/s.

Validation: maya-s24-turbo's `functest.py` **8/8** on both C and D (chat, forced tool call, zero-arg tool,
multi-turn with a tool result, SSE, vision, 17K-token needle, greedy); a 12-question checkable-answer probe
(`qprobe.py`) 12/12 on both.

For scale: the previous best GLM-5.3-Flash setup on this same machine (EXL3 2.05 bpw through an NVMe-offload
container) did 8.51 tokens/s.

## What the engine lines say

| run | disk reads/tok | disk wait ms/tok | VRAM hit | promotions/tok |
| --- | ---: | ---: | ---: | ---: |
| A stock | 28-36 | 77-117 | 79-83% | 33-40 |
| B turbo stack | 30-42 | 104-303 | 73-79% | 5-14 |
| C exact | 22-28 | 80-102 | 77-82% | 30-36 |
| D skip | 5-7 | 22-30 | 89-91% | 16-19 |

- **Decode is SSD-bound here**, not PCIe- or CPU-bound as on the reference rig: a token waits ~80-100 ms on
  ~25 random reads from a DRAM-less NVMe.
- **`PROMOTE_MIN=6` is the wrong lever without RAM residency.** It stops one-off experts churning VRAM slots,
  which pays when every miss is a 0.3 ms RAM fetch; when a miss is a disk read, keeping the expert in VRAM is
  what saves the next read. Promotions fell from ~35 to ~6 a token and decode from 11.7 to 8.0, prefill
  from 555 to 70 tokens/s.
- **`DISK_READERS=8`** (the project's own note for a Kingston NV3) is the exact lever that helps: prefill
  +34%/+18%, decode +4%.
- **`DISK_SKIP_W`** is the big one: experts that are on the SSD only and carry under 12% of a route's
  weight are left out (15-20 a token), and decode goes 12.2 → 29.1. It changes the output - the project
  measured KL 0.12 to the full computation at 0.12 (Maya-S itself is 0.43 from FP8) - and every check here
  still passes, but it is an approximation.
- Exact mode is also **unstable** here: the second production run of C fell to 6.2 tokens/s (2.6 on the
  code prompt) as the SSD queue backed up; D held 35.
- `--calibrate` with the turbo stack measured 1.4-7.6 tokens/s in noisy runs and kept the engine defaults.

## Verdict

- **Same as the tweet/repo? No.** The 50-60 tokens/s needs the experts that do not fit in 48 GB of VRAM to sit
  in RAM. With 32 GB of RAM the same engine, model and GPUs give 12 tokens/s exact, 29-35 approximate.
- **Usable? Yes, with D:** ~30 tokens/s decode, ~500-650 tokens/s prefill, tools, vision and a 17K needle all
  pass - 3.4× the previous GLM-5.3-Flash setup on this rig. Exact mode (C) is usable for short answers but
  swings between 6 and 15 tokens/s.
- **The cheapest next step is RAM**: 64 GB would hold most of the remaining ~30 GB of experts; at 128 GB the
  turbo stack (`RAM_RESIDENT=1`) applies as is. Moving GPU1 to an x16 slot would help the PCIe lane.

## Files

- `configs/` - the four engine configs (`env` blocks) as benched
- `logs/` - `--bench` output and the engine's stat lines per run, functest, production bench, sustained run
- `ctr.sh` - runs the setup/engine in a CUDA 13 container (no system CUDA toolkit, no sudo; the container
  also keeps the pinned-RAM engine out of the user slice's `systemd-oomd`)
- `runbench.sh` - one official bench with the current config, logs kept
- `qprobe.py` - the 12-question checkable-answer probe

Credits: the engine, the quant, the levers and the bench - **@mw00** and project-maya's contributors; the tuning
record, `bench.py` and `functest.py` - **@catonooka**.
