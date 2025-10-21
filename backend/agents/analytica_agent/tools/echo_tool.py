from google.adk.tools import Tool

class EchoTool(Tool):
    def __init__(self):
        super().__init__(
            name="echo_tool",
            description="Echoes the user's input. Used for testing.",
        )

    def __call__(self, query: str) -> str:
        """
        Takes a user's query and returns it as a response.
        Args:
            query: The input string from the user.
        Returns:
            The same input string, prefixed with 'Echo: '.
        """
        return f"Echo from Rumi-Analytica: {query}"