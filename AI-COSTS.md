# English Star — AI cost

**Bottom line:** at family scale the AI costs effectively nothing. The app's own hard cap of 50 uploads a day keeps the heaviest AI step inside Cloudflare's free daily allowance, even in the worst case. The one cost that can't be measured is the step that reads the photo, and that's what could push a heavy day over.

Figures below are calculations from the published prices and the limits enforced in the code. The app's admin dashboard records actual tokens, neurons and estimated cost per day; those measurements are the real check.

## How it's priced

| Item | Price |
|---|---|
| Model | `@cf/google/gemma-4-26b-a4b-it` on Cloudflare Workers AI |
| Input tokens | $0.10 per million (9,091 neurons per million) |
| Output tokens | $0.30 per million (27,273 neurons per million) |
| Free allowance | **10,000 neurons per day**, for every account, reset at 00:00 UTC |
| Above the free allowance | $0.011 per 1,000 neurons (Workers Paid plan only) |

"Neurons" is Cloudflare's own billing unit for Workers AI.

## Cost per worksheet upload

Each upload makes two model calls: the **AI judge** (should this material become a lesson?) and **lesson generation**.

| Case | Tokens in / out | Cost | Neurons |
|---|---|---|---|
| Typical one-page worksheet | ~4,000 / ~1,700 | ~$0.001 | ~85 |
| Worst case allowed by the limits | ~12,500 / ~2,850 | ~$0.002 | ~190 |

The worst case comes straight from the hard limits in code: at most 5,000 extracted tokens per upload, 350 output tokens for the judge and 2,500 output tokens for the lesson.

## Per day

| Scenario | Neurons | Billed |
|---|---|---|
| Normal family use (a few uploads) | ~400 | $0, inside the free 10,000 |
| Absolute ceiling: 50 uploads, all worst case | ~9,550 | $0, still under 10,000 |
| Hypothetical: the ceiling billed in full | — | ~$0.10/day, about $3/month |

## Limits that keep it this way

These are hard ceilings in code. Environment variables and the admin settings page can tune them, but never above the ceiling.

- 5 uploads per family per day, 50 per day for the whole app (reserved atomically, so they can't be raced)
- 2 MB per file, 5,000 extracted tokens, 2,500 output tokens
- Duplicate uploads are detected by content hash and never call the AI again
- Low-value uploads are rejected by the judge before the larger generation call

## Unknowns and edge cases

- **Reading the photo (`toMarkdown`).** Cloudflare doesn't publish a price for this conversion step. It probably consumes neurons too, which is what could push heavy days over the free 10,000.
- **What happens above the free allowance depends on the plan.** On the Workers Free plan nothing is billed: AI calls fail until 00:00 UTC, and uploads fall back to the admin review queue. On the Workers Paid plan the overage is billed at the rate above.
- **Fixed audio clips (OpenAI text-to-speech).** About 40 short clips are generated once and then served from storage. The one-time cost is likely a few cents.

## Sources

- [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)

---

[← Back to the English Star overview](README.md)
