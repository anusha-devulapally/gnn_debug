cd /home/labuser/anusha/gds_igb_baseline/gids_v4_spdk_parity_suite

OUT=~/anusha/gnn-debug/gnn-debug/prefetch_debug_dump_20261014.txt

mkdir -p ~/anusha/gnn-debug/gnn-debug

{
echo "========== DATE =========="
date

echo
echo "========== ACTIVE DIRECTORY =========="
pwd

echo
echo "========== CONFIRM SPLIT WORKER BINARY =========="
strings gids_v4_spdk_worker | grep -E \
'V4_SPLIT_DEMAND_DAX|V4_SPLIT_PREFETCH_DRAM|NUMA0_DRAM_CONTROL' \
|| true

echo
echo "========== PREFETCH SCATTER CALL SITES =========="

python3 - <<'PY'
from pathlib import Path

p = Path("gids_v4_spdk_parity.cu")
lines = p.read_text().splitlines()

keys = [
    "scatter_prefetch_explicit(",
    "pf_slots",
    "prefetch_slot",
    "PREFETCH_READY",
    "PF_READY",
    "PF_CONSUMING",
    "prefetch_page",
]

hits = []

for i, line in enumerate(lines):
    if any(k in line for k in keys):
        hits.append(i)

shown = set()

for i in hits:
    lo = max(0, i - 35)
    hi = min(len(lines), i + 55)

    key = (lo, hi)

    if key in shown:
        continue

    shown.add(key)

    print("\n" + "=" * 90)
    print(f"LINES {lo+1}-{hi}")
    print("=" * 90)

    for j in range(lo, hi):
        print(f"{j+1:5d}: {lines[j]}")
PY

echo
echo "========== WORKER PREFETCH REQUEST / COMPLETION =========="

python3 - <<'PY'
from pathlib import Path

p = Path("gids_v4_spdk_worker.c")
lines = p.read_text().splitlines()

keys = [
    "prefetch",
    "PREFETCH",
    "slot",
    "offset",
    "lba",
    "io_complete",
    "bdev_read",
    "spdk_bdev_read",
]

hits = []

for i, line in enumerate(lines):
    if any(k in line for k in keys):
        hits.append(i)

ranges = []

for i in hits:
    lo = max(0, i - 20)
    hi = min(len(lines), i + 35)

    if ranges and lo <= ranges[-1][1] + 10:
        ranges[-1] = (
            ranges[-1][0],
            max(ranges[-1][1], hi)
        )
    else:
        ranges.append((lo, hi))

for lo, hi in ranges:
    print("\n" + "=" * 90)
    print(f"LINES {lo+1}-{hi}")
    print("=" * 90)

    for j in range(lo, hi):
        print(f"{j+1:5d}: {lines[j]}")
PY

} 2>&1 | tee "$OUT"

echo
echo "SAVED OUTPUT TO:"
echo "$OUT"

cd ~/anusha/gnn-debug/gnn-debug

git status --short

git add prefetch_debug_dump_20261014.txt

if ! git diff --cached --quiet; then
    git commit -m "Add prefetch slot debug dump"
else
    echo "No new changes to commit"
fi

git push
