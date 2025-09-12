"""
Jira connector tool for watsonx Orchestrate.
Connects to actual Jira instance using REST API for incident management
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from typing import Dict, Any
import json
import requests
from datetime import datetime
import os
import base64

# Load environment variables

JIRA_INSTANCE_URL="https://your-instance.atlassian.net"
JIRA_USERNAME="your-email@company.com"
JIRA_API_TOKEN="YOUR_JIRA_API_TOKEN_HERE"
JIRA_PROJECT_KEY="YOUR_PROJECT_KEY"
JIRA_ISSUE_TYPE="Task"
JIRA_ASSIGNEE="your-email@company.com"
JIRA_PRIORITY_CRITICAL="Highest"
JIRA_PRIORITY_HIGH="High"
JIRA_PRIORITY_MEDIUM="Medium"
JIRA_PRIORITY_LOW="Low"

@tool(
    name="jira_connector_simple", 
    description="Create and manage Jira issues for Dish Network NOC operations via real Jira API",
    permission=ToolPermission.READ_WRITE
)
def manage_jira_issue(
    action: str,
    severity_level: str,
    outage_type: str,
    affected_nodes,  # Can be int or str
    issue_key: str = None,
    description: str = None,
    customer_impact: str = None,
    location: str = None
) -> str:
    """
    Create, update, or query Jira issues for network outages using real Jira REST API.
    
    Args:
        action: Action to perform (create, update, close, query)
        severity_level: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        outage_type: Type of outage (satellite, ground, fiber, power, equipment)
        affected_nodes: Number of affected network nodes or customers (int or str)
        issue_key: Existing issue key (for update/close actions, e.g., NOC-123)
        description: Detailed issue description
        customer_impact: Description of customer impact
        location: Geographic location or network area affected
    
    Returns:
        JSON string with Jira issue management results
    """
    
    # Get Jira configuration from hardcoded values
    instance_url = JIRA_INSTANCE_URL
    username = JIRA_USERNAME
    api_token = JIRA_API_TOKEN
    project_key = JIRA_PROJECT_KEY
    issue_type = JIRA_ISSUE_TYPE
    assignee = JIRA_ASSIGNEE
    
    # Jira API base URL
    base_url = f"{instance_url.rstrip('/')}/rest/api/3"
    
    # Create authentication headers
    auth_string = f"{username}:{api_token}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Basic {auth_b64}'
    }
    
    # Convert affected_nodes to integer if it's a string
    try:
        affected_nodes = int(affected_nodes) if affected_nodes else 0
    except (ValueError, TypeError):
        affected_nodes = 0
    
    # Map severity to Jira priority
    priority_mapping = {
        "CRITICAL": os.getenv('JIRA_PRIORITY_CRITICAL', 'Highest'),
        "HIGH": os.getenv('JIRA_PRIORITY_HIGH', 'High'),
        "MEDIUM": os.getenv('JIRA_PRIORITY_MEDIUM', 'Medium'),
        "LOW": os.getenv('JIRA_PRIORITY_LOW', 'Low')
    }
    
    # Add debug logging
    debug_info = {
        "action": action,
        "severity_level": severity_level,
        "outage_type": outage_type,
        "affected_nodes": affected_nodes,
        "description": description,
        "customer_impact": customer_impact,
        "location": location
    }
    
    try:
        if action.lower() == "create":
            result = _create_jira_issue(base_url, headers, severity_level, outage_type, affected_nodes, description, customer_impact, location, priority_mapping, project_key, issue_type, assignee)
            return result
        elif action.lower() == "update":
            return _update_jira_issue(base_url, headers, issue_key, description)
        elif action.lower() == "close":
            return _close_jira_issue(base_url, headers, issue_key, description)
        elif action.lower() == "query":
            return _query_jira_issue(base_url, headers, issue_key, project_key)
        else:
            return json.dumps({
                "error": f"Invalid action: {action}. Valid actions: create, update, close, query",
                "debug_info": debug_info
            })
    except Exception as e:
        return json.dumps({
            "error": f"Jira API error: {str(e)}",
            "action": action,
            "debug_info": debug_info,
            "timestamp": datetime.now().isoformat()
        })


def _create_jira_issue(base_url: str, headers: dict, severity_level: str, outage_type: str, affected_nodes: int, description: str, customer_impact: str, location: str, priority_mapping: dict, project_key: str, issue_type: str, assignee: str) -> str:
    """Create a new Jira issue via real Jira REST API."""
    
    # Build Jira issue payload
    priority_name = priority_mapping.get(severity_level.upper(), 'Medium')
    
    summary = f"Dish Network {outage_type.upper()} Outage"
    if location:
        summary += f" - {location}"
    summary += f" - {affected_nodes} Affected"
    
    if not description:
        description = f"""Network outage detected in Dish Network infrastructure.

*OUTAGE DETAILS:*
- Type: {outage_type.upper()} 
- Affected: {affected_nodes} nodes/customers
- Severity: {severity_level}
- Location: {location or 'Not specified'}
- Detection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

*IMPACT ASSESSMENT:*
{customer_impact or f'Service disruption affecting {affected_nodes} network elements'}

*NEXT ACTIONS:*
- NOC team investigating root cause
- Engineering teams notified for P1/P2 incidents  
- Customer communications prepared if needed
- Field operations on standby for equipment issues"""
    
    # Jira issue payload following Jira API v3 schema - simplified for basic fields only
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "issuetype": {
                "name": issue_type
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "labels": [
                "network-outage",
                f"severity-{severity_level.lower()}",
                f"type-{outage_type.lower().replace(' ', '-')}"
            ]
        }
    }
    
    # Only add assignee if we can resolve the account ID
    try:
        # Get user account ID from email
        user_search_url = f"{os.getenv('JIRA_INSTANCE_URL')}/rest/api/3/user/search"
        user_response = requests.get(user_search_url, headers=headers, params={"query": assignee}, timeout=30)
        if user_response.status_code == 200:
            users = user_response.json()
            if users:
                account_id = users[0].get('accountId')
                payload["fields"]["assignee"] = {"accountId": account_id}
    except Exception as e:
        print(f"Warning: Could not set assignee: {e}")
    
    # Add additional info in description since we can't use custom fields
    extended_description = f"""{description}

**SEVERITY:** {priority_name}
**CUSTOMER IMPACT:** {customer_impact or 'Not specified'}
**LOCATION:** {location or 'Not specified'}
**AFFECTED NODES:** {affected_nodes}"""
    
    payload["fields"]["description"]["content"][0]["content"][0]["text"] = extended_description
    
    try:
        # Call Jira REST API
        print(f"🔧 Creating Jira issue with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{base_url}/issue", json=payload, headers=headers, timeout=30)
        print(f"📡 Jira Response: {response.status_code} - {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            issue_key = result.get('key')
            issue_id = result.get('id')
            
            success_response = {
                "status": "success",
                "action": "create",
                "issue_key": issue_key,
                "issue_id": issue_id,
                "priority": priority_name,
                "assignee": assignee,
                "summary": summary,
                "created": datetime.now().isoformat(),
                "jira_url": f"{instance_url}/browse/{issue_key}",
                "message": f"✅ Issue {issue_key} created successfully in Jira"
            }
            print(f"✅ SUCCESS: {json.dumps(success_response, indent=2)}")
            return json.dumps(success_response)
        else:
            error_response = {
                "error": f"Failed to create issue: HTTP {response.status_code}",
                "details": response.text,
                "payload_sent": payload
            }
            print(f"❌ ERROR: {json.dumps(error_response, indent=2)}")
            return json.dumps(error_response)
            
    except requests.exceptions.RequestException as e:
        error_response = {
            "error": "Cannot connect to Jira instance",
            "details": str(e),
            "suggestion": "Check JIRA_INSTANCE_URL and network connectivity"
        }
        print(f"❌ CONNECTION ERROR: {json.dumps(error_response, indent=2)}")
        return json.dumps(error_response)


def _update_jira_issue(base_url: str, headers: dict, issue_key: str, comment: str) -> str:
    """Update an existing Jira issue via REST API."""
    
    if not issue_key:
        return json.dumps({"error": "issue_key is required for update action"})
    
    # Add comment to the issue
    comment_payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment or f"Issue updated by NOC automation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        # Add comment to the issue
        response = requests.post(f"{base_url}/issue/{issue_key}/comment", json=comment_payload, headers=headers, timeout=30)
        
        if response.status_code == 201:
            # Get updated issue details
            issue_response = requests.get(f"{base_url}/issue/{issue_key}", headers=headers, timeout=30)
            if issue_response.status_code == 200:
                issue_data = issue_response.json()
                return json.dumps({
                    "status": "success", 
                    "action": "update",
                    "issue_key": issue_key,
                    "summary": issue_data.get('fields', {}).get('summary'),
                    "status": issue_data.get('fields', {}).get('status', {}).get('name'),
                    "comment_added": comment,
                    "message": f"✅ Issue {issue_key} updated successfully",
                    "updated_on": datetime.now().isoformat(),
                    "jira_url": f"{os.getenv('JIRA_INSTANCE_URL')}/browse/{issue_key}"
                })
        
        return json.dumps({
            "error": f"Failed to update issue: HTTP {response.status_code}",
            "details": response.text
        })
            
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Cannot connect to Jira instance",
            "details": str(e)
        })


def _close_jira_issue(base_url: str, headers: dict, issue_key: str, resolution_comment: str) -> str:
    """Close a Jira issue via REST API."""
    
    if not issue_key:
        return json.dumps({"error": "issue_key is required for close action"})
    
    try:
        # First, get available transitions for the issue
        transitions_response = requests.get(f"{base_url}/issue/{issue_key}/transitions", headers=headers, timeout=30)
        
        if transitions_response.status_code != 200:
            return json.dumps({
                "error": f"Failed to get transitions: HTTP {transitions_response.status_code}",
                "details": transitions_response.text
            })
        
        transitions = transitions_response.json().get('transitions', [])
        
        # Look for a "Done", "Resolved", or "Closed" transition
        close_transition = None
        for transition in transitions:
            transition_name = transition.get('name', '').lower()
            if any(keyword in transition_name for keyword in ['done', 'resolved', 'closed', 'complete']):
                close_transition = transition
                break
        
        if not close_transition:
            return json.dumps({
                "error": "No suitable close transition found",
                "available_transitions": [t.get('name') for t in transitions]
            })
        
        # Add resolution comment if provided
        if resolution_comment:
            comment_payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Issue resolved by NOC team. Resolution: {resolution_comment}"
                                }
                            ]
                        }
                    ]
                }
            }
            requests.post(f"{base_url}/issue/{issue_key}/comment", json=comment_payload, headers=headers, timeout=30)
        
        # Transition the issue to closed state
        transition_payload = {
            "transition": {
                "id": close_transition.get('id')
            }
        }
        
        response = requests.post(f"{base_url}/issue/{issue_key}/transitions", json=transition_payload, headers=headers, timeout=30)
        
        if response.status_code == 204:
            # Get updated issue details
            issue_response = requests.get(f"{base_url}/issue/{issue_key}", headers=headers, timeout=30)
            if issue_response.status_code == 200:
                issue_data = issue_response.json()
                return json.dumps({
                    "status": "success",
                    "action": "close", 
                    "issue_key": issue_key,
                    "summary": issue_data.get('fields', {}).get('summary'),
                    "status": issue_data.get('fields', {}).get('status', {}).get('name'),
                    "resolution_comment": resolution_comment,
                    "message": f"✅ Issue {issue_key} closed successfully",
                    "resolved_on": datetime.now().isoformat(),
                    "jira_url": f"{os.getenv('JIRA_INSTANCE_URL')}/browse/{issue_key}"
                })
        
        return json.dumps({
            "error": f"Failed to close issue: HTTP {response.status_code}",
            "details": response.text
        })
            
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Cannot connect to Jira instance", 
            "details": str(e)
        })


def _query_jira_issue(base_url: str, headers: dict, issue_key: str = None, project_key: str = None) -> str:
    """Query Jira issues via REST API."""
    
    try:
        if issue_key:
            # Get specific issue
            response = requests.get(f"{base_url}/issue/{issue_key}", headers=headers, timeout=30)
            
            if response.status_code == 200:
                issue_data = response.json()
                fields = issue_data.get('fields', {})
                
                return json.dumps({
                    "status": "success",
                    "action": "query",
                    "issue": {
                        "key": issue_data.get('key'),
                        "id": issue_data.get('id'),
                        "summary": fields.get('summary'),
                        "status": fields.get('status', {}).get('name'),
                        "priority": fields.get('priority', {}).get('name'),
                        "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else 'Unassigned',
                        "created": fields.get('created'),
                        "updated": fields.get('updated'),
                        "description": _extract_text_from_adf(fields.get('description', {})),
                        "jira_url": f"{os.getenv('JIRA_INSTANCE_URL')}/browse/{issue_data.get('key')}"
                    },
                    "message": "✅ Issue data retrieved successfully"
                })
        else:
            # Search for recent issues in the project
            jql = f"project = {project_key} AND labels in (network-outage) ORDER BY created DESC"
            search_params = {
                'jql': jql,
                'maxResults': 10,
                'fields': 'summary,status,priority,assignee,created,updated'
            }
            
            response = requests.get(f"{base_url}/search", headers=headers, params=search_params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                issues = result.get('issues', [])
                formatted_issues = []
                
                for issue in issues:
                    fields = issue.get('fields', {})
                    formatted_issues.append({
                        "key": issue.get('key'),
                        "summary": fields.get('summary'),
                        "status": fields.get('status', {}).get('name'),
                        "priority": fields.get('priority', {}).get('name'),
                        "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else 'Unassigned',
                        "created": fields.get('created'),
                        "jira_url": f"{os.getenv('JIRA_INSTANCE_URL')}/browse/{issue.get('key')}"
                    })
                
                return json.dumps({
                    "status": "success",
                    "action": "query",
                    "issues": formatted_issues,
                    "count": len(formatted_issues),
                    "message": f"✅ Retrieved {len(formatted_issues)} issue(s) successfully"
                })
        
        return json.dumps({
            "error": f"Failed to query issue: HTTP {response.status_code}",
            "details": response.text
        })
            
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Cannot connect to Jira instance",
            "details": str(e)
        })

def _extract_text_from_adf(adf_content):
    """Extract plain text from Atlassian Document Format (ADF)."""
    if not adf_content or not isinstance(adf_content, dict):
        return ""
    
    text_parts = []
    content = adf_content.get('content', [])
    
    for item in content:
        if item.get('type') == 'paragraph':
            paragraph_content = item.get('content', [])
            for text_item in paragraph_content:
                if text_item.get('type') == 'text':
                    text_parts.append(text_item.get('text', ''))
    
    return ' '.join(text_parts)
