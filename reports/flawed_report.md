# Harness Evaluation Report — `flawed`

**Generated:** 2026-08-31T14:27:08+00:00  
**Overall score:** 0.7937

## Metric breakdown

| Metric | Mean score | 95% CI | Weight |
| --- | --- | --- | --- |
| correctness | 0.750 | ±0.200 | 0.3 |
| failure_rate | 0.800 | ±0.000 | 0.2 |
| consistency | 0.750 | ±0.200 | 0.15 |
| structured_output | 0.938 | ±0.122 | 0.1 |
| tool_calling | 0.812 | ±0.367 | 0.1 |
| latency | 0.640 | ±0.146 | 0.08 |
| cost | 1.000 | ±0.000 | 0.07 |

## Failed cases

- **strict_json_schema** (structured): latency=0.481
- **multi_tool_call** (tool_use): tool_calling=0.25

## Recommendations

- Low correctness: revisit prompts/few-shot examples for the failing categories.
- Low consistency: lower temperature or constrain outputs for deterministic tasks.
- High p95 latency: consider a faster model tier, caching, or shorter prompts.
