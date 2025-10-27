import os
from google.adk.agents import Agent

ANALYTICS_INSTRUCTIONS = """
You are a world-class data analyst. 
Your goal is to help users by answering their questions about data.
To do this, you will write and execute Python code using the provided code executor tool.
Analyze the user's request, write the necessary code, and then interpret the results to provide a clear, natural language answer.
"""

root_agent = Agent(
    # The 'name' parameter inside the Agent should match your folder name
    # for consistency, though 'root_agent' is the critical variable name.
    name="rumi_analytica",

    # Use an environment variable for the model, with a sensible default.
    model=os.getenv("ANALYTICS_AGENT_MODEL", "gemini-2.5-flash"),

    # Keep complex instructions in a separate file or function for cleanliness.
    instruction=ANALYTICS_INSTRUCTIONS,
    description="An agent for performing data analysis by writing and executing Python code.", 
)