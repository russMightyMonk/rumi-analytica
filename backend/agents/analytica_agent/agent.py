from google.adk.agents import Agent
from .tools.echo_tool import EchoTool

def create_agent() -> Agent:
    """Create the Analytica Agent."""
    return Agent(
        # The name must match the folder name
        name="analytica_agent",
        description="An agent for answering questions about analytics.",
        tools=[EchoTool()],
    )