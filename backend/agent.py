from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LoopAgent
from google.adk.apps import App
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from .itinerary_agent import itinerary_agent
from .evaluator_agent import evaluator_agent

class EscalationChecker(BaseAgent):
    """Stops a LoopAgent when evaluation criteria are met."""
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        result = ctx.session.state.get("evaluation_result")
        if result and result.get("passed") is True:
            # Clear feedback instruction if passed successfully
            ctx.session.state["feedback_instruction"] = ""
            yield Event(author=self.name, actions=EventActions(escalate=True))
        elif result:
            feedback = result.get("feedback", "")
            score = result.get("score", 0.0)
            # Inject feedback into state for the next itinerary_agent run
            ctx.session.state["feedback_instruction"] = f"""
CRITICAL: Your previous itinerary proposal was evaluated and DID NOT pass our quality standards (Score: {score}).
Please refine and correct the itinerary to address the following feedback:
--- FEEDBACK ---
{feedback}
----------------
Ensure your next output is a fully complete, improved ItineraryProposal JSON addressing these points precisely.
"""
            yield Event(author=self.name)
        else:
            yield Event(author=self.name)

escalation_checker = EscalationChecker(name="escalation_checker")

# Root agent is a LoopAgent combining the planner, evaluator, and escalation checker
root_agent = LoopAgent(
    name="itinerary_refinement_loop",
    sub_agents=[itinerary_agent, evaluator_agent, escalation_checker],
    max_iterations=3,
)

app = App(
    name="app",
    root_agent=root_agent,
)
