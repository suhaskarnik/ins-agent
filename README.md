This project creates an insurance claim triage agent. Its job is to do the following:

1. Intake a mocked input of Policy and Claim information. Both of these could be complete or incomplete. Imagine that a user has provided these details in a form while submitting the claim. They may provide correct, incorrect, complete or incomplete information
2. An LLM searches the Policy in a PG Database. Depending on what was provided in the input, this could be a simple `WHERE policy_id = :input_policy_id` or be more involved. This optimises for recall
3. A deterministic ranker optimises for precision by weight-wise scoring the provided inputs. An exact policy match with a name match receives a perfect score, others with proportionately lower weights. Use Jaro-Winkler and Metaphone and phone canonicalisation as well, assign proprtionately lower weights. A tunable threshold score is applied. Top N (configurable, default 3) ranks go forward. If all the results are low quality (below threshold), return to step 2. Repeat at most 3 times, and if no policy is found, trigger the final HITL. 
4. If exactly 1 policy was ranked, or there is any policy with a perfect score, then pick that policy and go to the next step. Otherwise, invoke a human approval interrupt to select a single policy. Failure to choose a policy would trigger the final HITL step
5. LLM checks eligibility of the claim for the policy. Use a processing guideline document that describes completeness reqs. This document should be part of the agent config, not provided by the user. Ineligible claims are routed to the final HITL step
6. LLM checks documentation provided for the claim and assesses if docs provided are sufficient or incomplete 
7. Final HITL step: LLM reports to a human operator about the outcome (claim is sufficient/incomplete, eligible/ineligible, policy found with high/low confidence), and suggests the next action along with the email comm wording. If human approves the action, then the email is triggered
8. No concrete implementation of email required; just write the text to a temp dir and print the output
9. No UI required; barebones TUI using input() statements is fine

Libraries used:
- langgraph
- langchain
- pydantic (for structured outputs)
- psycopg2
- langfuse


LLM Providers:
- groq, with multiple models that will be selected in a `.env`. Should be swappable to openrouter without changing the rest of the code
- model config should follow some classes, such as `model_high: ["claude opus 5", "gpt-5.6 sol"]`, with each archetype being chosen based on the task. This is to avoid expensive models being used for trivial tasks
- the classes do not need to be literally called `model_high`, a different set of classnames can be chosen that is appropriate for this use case


Key Principles:
- no payment or comms go to the user before a human gate
- to avoid overwhelming the human, ensure that most of the tedious searching and matching is done before the result reaches the human
- to enable correct decision making, ensure that details provided to the human are valid. Ideally this should be deterministic, but when it is not, that should be clearly specified in the final output to the human verifier.  Deterministic and non-deterministic outputs should NOT be mixed and presented as though they are at equivalent levels of veracity
- all LLM calls and outputs are logged using Langfuse
- no credentials in code, use a `.env` file instead
- all parameters like the tuning threshold, the model classes, Postgres hostname etc are in the .env file. Whenever the .env contract changes, a .env.example should be created/updated to reflect the reqd params
- pass data across steps using structured Pydantic objects. Avoid plaintext except at entry, to prevent injection attacks
- system prompts to be managed as MD files in the repo, and git-versioned
