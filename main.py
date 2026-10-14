cd /home/labuser/anusha/gds_igb_baseline/gids_v4_spdk_parity_suite

python3 - <<'PY' > /tmp/prefetch_lifecycle_report.txt
from pathlib import Path
import re

files = {
    "CUDA": Path("gids_v4_spdk_parity.cu"),
    "WORKER": Path("gids_v4_spdk_worker.c"),
}

patterns = {
    "CUDA": [
        # State definitions / transitions
        r'PF_[A-Z_]+',
        r'PREFETCH_[A-Z_]+',
        r'prefetch.*state',
        r'state.*prefetch',

        # Slot -> page bookkeeping
        r'prefetch.*slot',
        r'slot.*prefetch',
        r'prefetch.*page',
        r'page.*prefetch',

        # Request submission / completion consumption
        r'prefetch.*enqueue',
        r'prefetch.*complete',
        r'prefetch.*ready',
        r'prefetch.*consume',
        r'inflight',

        # Actual use / release
        r'scatter_prefetch_explicit',
        r'pf_slots',
        r'free.*slot',
        r'release.*slot',
        r'slot.*free',

        # Synchronization
        r'atomic',
        r'memory_order',
        r'fence',
    ],

    "WORKER": [
        # Request fields
        r'prefetch',
        r'PREFETCH',

        # Slot + SSD offset association
        r'slot',
        r'offset',
        r'lba',

        # Submission/completion
        r'bdev.*read',
        r'spdk_bdev_read',
        r'io_complete',
        r'completion',
        r'complete',

        # Request struct / protocol
        r'struct .*req',
        r'struct .*cmd',
        r'OP_',
    ],
}

for label, path in files.items():
    lines = path.read_text(errors="replace").splitlines()

    print()
    print("=" * 100)
    print(label, path)
    print("=" * 100)

    hits = []

    for i, line in enumerate(lines):
        if any(re.search(p, line, re.I) for p in patterns[label]):
            hits.append(i)

    # Merge nearby matches to avoid giant repetitive output.
    ranges = []

    for i in hits:
        lo = max(0, i - 3)
        hi = min(len(lines), i + 4)

        if ranges and lo <= ranges[-1][1] + 2:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], hi))
        else:
            ranges.append((lo, hi))

    # Limit to keep report manageable.
    for lo, hi in ranges[:35]:
        print(f"\n--- lines {lo+1}-{hi} ---")
        for j in range(lo, hi):
            print(f"{j+1:5d}: {lines[j]}")

print()
print("=" * 100)
print("ACTIVE VARIANT")
print("=" * 100)

cu = files["CUDA"].read_text(errors="replace")
wk = files["WORKER"].read_text(errors="replace")

for x in [
    "SPDK_BDEV_AIO_DRAM_INGRESS_COHERENT_H2D_DAX_GPU",
    "V4_DRAM_PREFETCH_COHERENT_STAGE",
    "V4_SPLIT_DEMAND_DAX_MAP_PASS",
    "V4_SPLIT_PREFETCH_DRAM_MAP_PASS",
]:
    print(f"{x}: {'YES' if (x in cu or x in wk) else 'NO'}")
PY

wc -l /tmp/prefetch_lifecycle_report.txt
cat /tmp/prefetch_lifecycle_report.txt

grep -nEi \
'PF_|prefetch.*state|state.*prefetch|prefetch.*slot|slot.*prefetch|prefetch.*page|page.*prefetch|READY|CONSUM|FREE|scatter_prefetch|io_complete|completion|bdev.*read|offset|lba|atomic|memory_order' \
/tmp/prefetch_lifecycle_report.txt
