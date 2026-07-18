# Frontend Architecture & Rules

This is the frontend client and admin dashboard for the **AI-Driven Travel Itinerary Planner**.

## Tech Stack & Design System
- **Build Tool:** Vite
- **Logic:** Vanilla JavaScript / HTML5
- **Styling:** Vanilla CSS (no TailwindCSS or frameworks unless explicitly requested).
- **Icons / Fonts:** Google Fonts (Inter, Outfit) and custom smooth SVG/CSS icons.

## Design Aesthetics (Mandatory)
1. **Rich & Modern Aesthetics:** Visuals must feel premium, using sleek dark mode palettes, harmonious gradients, and glassmorphism.
2. **Micro-animations:** Hover transitions, active state scaling, and loading state animations are required to make the UI feel alive and premium.
3. **Responsive & Fluid:** Grid and flex layouts must adapt gracefully from desktop down to mobile viewports.
4. **No Placeholders:** All functional views, loading skeletons, and interactive states must be fully fleshed out with dynamic demo content rather than generic placeholders.

## State Management & Polling
1. **Asynchronous Polling:** Since travel agent planning (using live Search) can take up to 20-30 seconds, implement an elegant, state-driven polling mechanism or WebSocket connection tracking `/api/status`.
2. **Loading States:** Provide beautiful progress indicators and custom text animations matching the standard backend real-time execution steps:
   - `"Initializing Agent..."`: Starting the reasoning thread.
   - `"Querying Google Search..."`: Sourcing real-world grounding data for flights, lodging, or attractions.
   - `"Formulating Proposal..."`: Assembling the structured travel plan.
   - `"Running Evaluator Check..."`: Scoring the proposal via the Gemini Flash LLM-as-a-judge quality gate.
   - `"Refining Itinerary..."` (if evaluation score falls below threshold): Incorporating judge feedback.
   - `"Awaiting Admin Review..."`: Successfully written to Firestore as pending.
   - `"Approved!"` / `"Rejected"`: Based on HITL dashboard actions.
