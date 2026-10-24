# Threadly — Evaluation Coverage Review

**What we did:** Reviewed everything the project currently uses to judge if Tia (the agent) is working well, and compared it against what a real customer-support agent should be tested on.

## What's working

- We have a rubric with 7 quality dimensions (intent recognition, grounding, policy compliance, tool selection, escalation, conversation quality, context retention).
- We have 400 reference test conversations covering all 16 customer intents (tracking, delays, returns, exchanges, damaged items, cancellations, etc.).
- Intent recognition is auto-scored today: **75.8% accuracy** on the test set (Demo mode baseline).

## Gaps found

1. **Only 1 of the 7 rubric dimensions is actually auto-scored.** The other 6 (grounding, policy compliance, tool use, escalation, tone, context retention) are marked "needs manual review" every single run — nobody is currently checking them automatically, even though the data to do so already exists in our files.
2. **We can't test "does Tia remember earlier in the conversation?" at all.** Every test case today is a single message, not a back-and-forth chat. This is the "conversation continuity" gap your team flagged — there's currently no way to measure it.
3. **"Does Tia ask unnecessary questions?" isn't tracked** as a dimension anywhere yet — also something the team asked for.
4. **The damaged-item scenario is accidentally skipped** by our standard test run (it exists in the data, just not in the slice we evaluate by default).
5. **The new order scenarios we just added** (cancellable orders, partial deliveries, previously-flagged damaged/wrong items) **aren't covered by any test case yet**, so we can't prove the new behavior keeps working as we keep changing things.
6. **No tests for bad actors** — e.g., someone trying to manipulate Tia with fake instructions, or trying to look up someone else's order. The agent is designed to block these, but nothing currently checks that it actually does.

## Recommended next steps (in priority order)

1. Turn on auto-scoring for escalation and tool-selection — quick win, data already exists.
2. Add a small set of multi-turn conversations to finally test "does Tia remember context."
3. Add test cases for the new order scenarios we just built, plus a damaged-item case in the standard test run.
4. Add a handful of "trying to break it" test cases (fake instructions, wrong customer accessing another's order).

No code has been changed yet — this is a review only, for discussion with the team before we prioritize what to build.
