from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

ROOT_CAUSE_KEYWORDS = {
    "Backhaul Failure": ["fiber cut", "link failure", "carrier loss", "backhaul"],
    "Power Outage": ["power", "UPS", "battery", "generator", "electricity"],
    "Configuration Error": ["bgp", "acl", "config", "routing", "misconfig", "policy"]
}

@tool(
    name="diagnose_incident_log",
    description="Analyzes a log message and tags the most likely root cause (e.g. power outage, config error, backhaul issue).",
    permission=ToolPermission.ADMIN
)
def diagnose_incident_log(log_message: str) -> str:
    """
    Takes in a log message and returns a basic root cause tag based on keyword matching.
    """
    log_lower = log_message.lower()
    for cause, keywords in ROOT_CAUSE_KEYWORDS.items():
        if any(keyword in log_lower for keyword in keywords):
            return cause
    return "Unknown"

##Sample Logs
# "Site S005 is unreachable. Fiber cut detected between router R03 and R04. Escalated to backhaul team.",
# "UPS unit failed at site S002. Generator did not auto-start. Site running on battery only.",
# "BGP session dropped due to incorrect neighbor settings in config push from NOC.",
# "Ping lost, link failure, to site S008. Investigating further..."