# Phase 2: Core Agent Logic (Primary Agent)

**Goal:** Implement the primary generative travel agent using Gemini 3.1 Pro and the Google Agent Development Kit (ADK).

**Tasks:**
- [x] 1. Implement the primary travel agent using Gemini 3.1 Pro via the ADK in the `backend/` directory.
- [x] 2. Integrate the **Google Search tool** into the agent's capabilities.
- [x] 3. Implement fallback strategies for tool failure (e.g., if Google Search returns no results, the agent should ask the user to broaden criteria rather than hallucinating).
- [x] 4. Define the system prompt and structured output schema for the itinerary proposals.

**Definition of Done:** A functional Python script/module that can take a travel request and output a structured itinerary using Google Search.
