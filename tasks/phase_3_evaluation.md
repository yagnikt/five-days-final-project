# Phase 3: Evaluation Layer (LLM-as-a-Judge) & Security

**Goal:** Implement the evaluation agent, the loop logic, and security guardrails.

**Tasks:**
1. Implement the evaluator agent using Gemini 3.5 Flash in `backend/evaluator_agent.py`.
2. Create an evaluation prompt to score the primary agent's output based on feasibility, quality, and adherence to constraints.
3. **Loop Logic & Cost Control:** Implement the logical loop inside the API routing layer: if the judge's score is below a threshold, prompt the primary agent to refine. Include a `max_retries` counter to prevent infinite loops.
4. **Offline Evaluation (CI/CD Gates):** Configure the evaluation metrics using `agents-cli` and run automated regression checks against `.evalset.json` test cases via `agents-cli eval run`. Ensure the model baseline passes the quality threshold before committing.
5. **Security Guardrails:**
   - Configure Vertex AI Safety Settings for the Pro agent to block harmful injections.
   - Implement input validation on the backend service to sanitize and delimit user requests.

**Definition of Done:** An evaluation module that wraps the primary agent, securely processes input, runs automated offline evaluations using `agents-cli eval`, and ensures runtime outputs meet quality standards.
