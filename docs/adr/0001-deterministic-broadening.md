# Deterministic broadening instead of LLM-directed retry

When Recall's candidates all fall below the Match Threshold, the obvious design is to feed the LLM feedback on the failed attempt and let it decide how to loosen its own search. We rejected that: broadening instead follows a fixed sequence (drop DOB/phone → name-only fuzzy) regardless of what the LLM thinks.

The trade-off is real — an adaptive LLM-directed retry could in principle find matches the fixed sequence misses. We chose predictability and testability instead: a fixed sequence means the retry path is fully covered by the Scenario suite and never surprises a reviewer with an unexplainable third attempt. The LLM's judgment is reserved for constructing the *initial* query from messy Intake Input, not for deciding retry strategy.
