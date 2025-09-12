"""
Simple email notification tool for watsonx Orchestrate.
Sends real emails via Gmail SMTP.
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from typing import Dict, Any
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import traceback


# Gmail SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "YOUR_APP_SPECIFIC_PASSWORD"  # App-specific password
DEFAULT_RECIPIENT = "recipient@company.com"


@tool(
    name="email_notification_simple",
    description="Send real email notifications for Dish Network NOC incidents and outages via Gmail",
    permission=ToolPermission.READ_WRITE
)
def send_outage_notification(
    severity_level: str,
    outage_type: str,
    affected_nodes: int,
    recipient_email: str = None,
    incident_number: str = None,
    include_details: bool = True
) -> str:
    """
    Send real email notification for network outage incidents.
    
    Args:
        severity_level: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        outage_type: Type of outage (satellite, ground, fiber, power)
        affected_nodes: Number of affected network nodes or customers
        recipient_email: Email address to send to (defaults to IBM email)
        incident_number: ServiceNow incident number if available
        include_details: Whether to include detailed technical information
    
    Returns:
        JSON string with email sending status and details
    """
    
    # Use default recipient if none specified
    recipient = recipient_email or DEFAULT_RECIPIENT
    
    try:
        # Generate email subject
        subject = f"🚨 [{severity_level}] Dish Network {outage_type.upper()} Outage"
        if incident_number:
            subject += f" - {incident_number}"
        subject += f" - {affected_nodes:,} Affected"
        
        # Generate email body
        body_content = _generate_email_body(
            severity_level, outage_type, affected_nodes, incident_number, include_details
        )
        
        # Send the actual email
        email_result = _send_email(recipient, subject, body_content)
        
        if email_result["status"] == "success":
            return json.dumps({
                "notification_status": "sent",
                "email_details": {
                    "subject": subject,
                    "recipient": recipient,
                    "priority": "high" if severity_level in ["CRITICAL", "HIGH"] else "normal",
                    "timestamp": datetime.now().isoformat(),
                    "message_id": email_result.get("message_id"),
                    "incident_number": incident_number
                },
                "delivery_info": {
                    "delivery_method": "Gmail SMTP",
                    "delivery_status": "sent",
                    "sender": SENDER_EMAIL
                },
                "message": f"✅ Email sent successfully to {recipient}"
            }, indent=2)
        else:
            return json.dumps({
                "notification_status": "failed",
                "error": email_result.get("error"),
                "email_details": {
                    "subject": subject,
                    "recipient": recipient,
                    "timestamp": datetime.now().isoformat()
                }
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "notification_status": "error",
            "error": f"Failed to send email: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc()
        }, indent=2)


def _send_email(recipient: str, subject: str, body: str) -> dict:
    """Send email via Gmail SMTP."""
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient, text)
        server.quit()
        
        return {
            "status": "success",
            "message": f"Email sent to {recipient}",
            "message_id": f"dish-noc-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def _generate_email_body(severity_level: str, outage_type: str, affected_nodes: int, incident_number: str, include_details: bool) -> str:
    """Generate email body content based on outage details."""
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    base_body = f"""🚨 DISH NETWORK OPERATIONS CENTER ALERT 🚨

INCIDENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 Severity: {severity_level}
📡 Outage Type: {outage_type.upper()}
👥 Affected: {affected_nodes:,} customers/nodes
⏰ Detection Time: {current_time}
🎫 Incident Number: {incident_number or 'Not assigned'}

STATUS: 🔴 ACTIVE INCIDENT

SUMMARY:
A {outage_type} outage has been detected affecting {affected_nodes:,} network elements.
This incident has been classified as {severity_level} priority and requires immediate attention.

IMMEDIATE ACTIONS REQUIRED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    # Add severity-specific actions
    if severity_level == "CRITICAL":
        base_body += """
🚨 CRITICAL RESPONSE PROTOCOL:
• IMMEDIATE escalation to senior NOC engineer
• Page on-call infrastructure team
• Activate emergency response procedures
• Prepare customer communication
• Notify executive management
• Dispatch field technicians if required"""
    elif severity_level == "HIGH":
        base_body += """
⚠️ HIGH PRIORITY RESPONSE:
• Escalate to NOC supervisor immediately
• Notify infrastructure team
• Monitor for further degradation
• Prepare customer status update
• Review backup systems"""
    else:
        base_body += """
📋 STANDARD RESPONSE:
• Continue monitoring situation
• Log incident details thoroughly
• Apply standard response procedures
• Keep stakeholders informed"""
    
    if include_details:
        base_body += f"""

TECHNICAL DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Detection System: Automated NOC Monitoring
🌐 Affected Services: Network Infrastructure
📍 Geographic Impact: Multiple regions
🛠️ ServiceNow Incident: {incident_number or 'Being created'}
📊 Network Availability: Degraded"""
    
    base_body += f"""

CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 NOC Team: NOC Operations Center
📱 Emergency Line: +1-XXX-XXX-XXXX
🌐 ServiceNow Dashboard: http://localhost:8083
⏰ Next Update: Within 30 minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated notification from Dish Network NOC System.
Generated at: {current_time}
Sent via: IBM watsonx Orchestrate Agent System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return base_body.strip()


# Test function for standalone testing
if __name__ == "__main__":
    # Test the email tool
    print("🧪 Testing email notification...")
    result = send_outage_notification(
        severity_level="HIGH",
        outage_type="satellite",
        affected_nodes=50000,
        incident_number="INC0001002",
        include_details=True
    )
    print("Email Result:")
    print(result)
