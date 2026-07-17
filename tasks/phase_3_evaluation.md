# Phase 3: Evaluation Layer (LLM-as-a-Judge) & Security

**Goal:** Implement the evaluation agent, the loop logic, and security guardrails.

**Tasks:**
1. Implement the evaluator agent using Gemini 3.5 Flash.
2. Create an evaluation prompt to score the primary agent's output based on feasibility, quality, and adherence to constraints.
3. **Loop Logic & Cost Control:** Implement the logical loop: if the judge's score is below a threshold, prompt the primary agent to refine. Include a `max_retries` counter to prevent infinite loops.
4. **Security Guardrails:**
   - Configure Vertex AI Safety Settings for the Pro agent to block harmful injections.
   - Implement input validation on the backend service to sanitize and delimit user requests.

**Definition of Done:** An evaluation module that wraps the primary agent, securely processes input, and ensures the output meets quality standards.
