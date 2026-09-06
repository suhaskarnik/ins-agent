# Postgres-backed checkpointer for durable human-in-the-loop gates

The Policy Selection Gate and Final Review Gate both pause the graph via LangGraph's `interrupt()`, which requires a checkpointer. We chose a Postgres-backed checkpointer over the in-memory default.

An in-memory checkpointer is the simpler default for a POC, and would work fine for a single unattended demo run. We rejected it because a human gate that only survives within one running process isn't really a human gate — a reviewer should be able to walk away and resume triage later, which is the entire point of pausing on a human rather than blocking on one. Since Postgres is already a hard dependency for Policy/Claim data, this adds durability at near-zero infrastructure cost.
