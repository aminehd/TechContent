# Video Generation Commands

```bash
cd ~/workplace/Viz
```

## Sliding Window

```bash
python3 -m viz_framework.run solutions/lc003_sliding_window.py longest_substring '"abcabcbb"' \
    --record videos/lc003_sliding_window.mp4 --shorts --fps 1.5 --context-lines 10
```

```bash
python3 -m viz_framework.run solutions/lc030_sliding_window.py find_substring '"barfoothefoobarman"' '["foo","bar"]' \
    --record videos/lc030_sliding_window.mp4 --shorts --fps 1.5 --context-lines 10
```

## Kadane's DP

```bash
python3 -m viz_framework.run solutions/lc053_kadanes_dp.py max_subarray '[-2,1,-3,4,-1,2,1,-5,4]' \
    --record videos/lc053_kadanes_dp.mp4 --shorts --fps 1.5 --context-lines 10
```

## Sort + Greedy

```bash
python3 -m viz_framework.run solutions/lc056_sort_greedy.py merge '[[1,3],[2,6],[8,10],[15,18]]' \
    --record videos/lc056_sort_greedy.mp4 --shorts --fps 1.5 --context-lines 10
```

## Prefix / Suffix

```bash
python3 -m viz_framework.run solutions/lc238_prefix_suffix.py product_except_self '[1,2,3,4]' \
    --record videos/lc238_prefix_suffix.mp4 --shorts --fps 1.5 --context-lines 10
```

## Two Pointers

```bash
python3 -m viz_framework.run solutions/lc011_two_pointers.py max_water '[1,8,6,2,5,4,8,3,7]' \
    --record videos/lc011_two_pointers.mp4 --shorts --fps 1.5 --context-lines 10
```

```bash
python3 -m viz_framework.run solutions/lc015_two_pointers.py three_sum '[-1,0,1,2,-1,-4]' \
    --record videos/lc015_two_pointers.mp4 --shorts --fps 1.5 --context-lines 10
```

```bash
python3 -m viz_framework.run solutions/lc167_two_pointers.py two_sum '[2,7,11,15]' 9 \
    --record videos/lc167_two_pointers.mp4 --shorts --fps 1.5 --context-lines 10
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--shorts` | off | 1080×1920, font 28pt, stacked layout (YouTube Shorts) |
| `--fps N` | 2.0 | frames per second |
| `--context-lines N` | 3 | source lines shown above/below cursor |
| `--rec-width` / `--rec-height` | 1920/1080 | custom resolution (no `--shorts`) |
| `--font-size N` | auto | override font size in pt |
| `--auto --speed N` | — | interactive viewer instead of recording |
