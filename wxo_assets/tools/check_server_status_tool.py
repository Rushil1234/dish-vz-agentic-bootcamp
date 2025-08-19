from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
import requests

@tool(
    name="check_server_status",
    description="Checks whether a given server (HTTP/HTTPS endpoint) is up or down by sending an HTTP GET request.",
    permission=ToolPermission.ADMIN
)
def check_server_status(url: str) -> str:
    """
    Takes a server address (URL) and returns whether the HTTP service is reachable.
    Returns 'UP' for status codes < 400, otherwise 'DOWN'.
    """
    if not url.startswith("http"):
        url = "https://" + url  # Default to HTTPS if not included

    try:
        response = requests.get(url, timeout=5)
        if response.status_code < 400:
            return f"{url} is UP (status code {response.status_code})"
        else:
            return f"{url} is DOWN (status code {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"{url} is DOWN (error: {e})"
