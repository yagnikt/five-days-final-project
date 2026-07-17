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
1. **Asynchronous Polling:** Since travel agent planning (using live Search) can take up to 20-30 seconds, implement a elegant, state-driven polling mechanism or WebSocket connection.
2. **Loading States:** Provide beautiful progress bar updates or custom text animations indicating what step the planner is currently on (e.g., "Researching flight options...", "Evaluating constraints...").
