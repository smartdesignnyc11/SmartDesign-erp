# Cost of the run, per day

Measured = the token counts the conductor copied from each subagent's result (`simctl cost`). Estimated = the harness's own count (calls, characters in and out) with a fixed 10k-token overhead per call assumed. Read the measured column; the estimate stands in for turns with no measurement.

| Day | Turns | Calls | Measured turns | Measured tokens | Tool uses | Agent minutes | Est. processed input | Est. new context | Est. output |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-03 | 21 | 252 | 21 | 1,644,542 | 287 | 26 | 5,018,280 | 215,058 | 78,792 |
| 2026-09-04 | 22 | 288 | 22 | 1,778,911 | 314 | 31 | 7,039,111 | 314,060 | 90,359 |
| 2026-09-08 | 47 | 336 | 47 | 4,213,873 | 441 | 46 | 9,572,865 | 469,225 | 112,700 |

| Day | Slot | Turns | Measured tokens | Est. processed input |
|---|---|---|---|---|
| 2026-09-03 | morning | 7 | 509,468 | 1,380,398 |
| 2026-09-03 | work | 7 | 558,815 | 2,296,194 |
| 2026-09-03 | eod | 7 | 576,259 | 1,341,688 |
| 2026-09-04 | morning | 7 | 558,905 | 1,835,668 |
| 2026-09-04 | work | 7 | 515,639 | 3,298,871 |
| 2026-09-04 | after | 1 | 94,611 | 0 |
| 2026-09-04 | eod | 7 | 609,756 | 1,904,572 |
| 2026-09-08 | morning | 9 | 759,049 | 2,622,158 |
| 2026-09-08 | work | 9 | 761,947 | 3,768,837 |
| 2026-09-08 | eod | 9 | 816,760 | 3,181,870 |
| 2026-09-08 | after | 20 | 1,876,117 | 0 |
