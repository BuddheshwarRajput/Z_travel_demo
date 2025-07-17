from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator
from typing_extensions import override
from .sub_agents.authenticator_agent.agent import authenticator_agent
from .sub_agents.orchestrator_agent.agent import orchestrator_agent
from .sub_agents.fallback_agent.agent import fallback_agent

class ManagerAgent(BaseAgent):
    """
    The root agent (CEO) of the chatbot. Its ONLY job is to manage the user's
    session state by routing them based on their authentication status.
    It is simple, robust, and doesn't handle any specific tasks itself.
    """
    authenticator_agent: BaseAgent
    
    fallback_agent: BaseAgent
    orchestrator_agent: BaseAgent

    def __init__(self, name: str):
        super().__init__(
            name=name,
            authenticator_agent=authenticator_agent,
            orchestrator_agent= orchestrator_agent,
            fallback_agent=fallback_agent,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Directs the entire conversation based on a single, critical piece of state:
        'user_authenticated'.
        """
        try:
            if not ctx.session.state.get("user_authenticated"):
                async for event in self.authenticator_agent.run_async(ctx):
                    yield event
            else:
                async for event in self.orchestrator_agent.run_async(ctx):
                    yield event

        except Exception as e:
            print(f"!! FALLBACK TRIGGERED !! An error occurred in the top-level Manager. Error: {e}")
            async for event in self.fallback_agent.run_async(ctx):
                yield event

root_agent = ManagerAgent(name="ManagerAgent")