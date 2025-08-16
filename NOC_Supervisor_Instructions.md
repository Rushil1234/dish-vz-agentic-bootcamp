# Use case: NOC Supervisor Assistant

## Table of Contents

- [Use case: NOC Supervisor Assistant](#use-case-noc-supervisor-assistant)  
  - [Table of Contents](#table-of-contents)  
  - [Introduction](#introduction)  
    - [Pre-requisites](#pre-requisites)  
  - [watsonx Orchestrate (SaaS)](#watsonx-orchestrate-saas)  
    - [The watsonx Orchestrate console](#the-watsonx-orchestrate-console)  
    - [AI Agent Configuration](#ai-agent-configuration)  
    - [The Network Status Agent](#the-network-status-agent)  
    - [The Server Status Agent](#the-server-status-agent)  
    - [The Incident Diagnosis Agent](#the-incident-diagnosis-agent)  
    - [The Communications Agent](#the-communications-agent)  
    - [The NOC Supervisor Agent](#the-noc-supervisor-agent)  
  - [Summary](#summary) 

## Introduction  

This use case describes a scenario where a Network Operations Center (NOC) Supervisor leverages an AI assistant through a natural language chat interface to investigate, diagnose, and resolve service disruptions. The assistant acts as a central routing point that selects the appropriate specialized agent to satisfy each request, ensuring rapid coordination across tools and knowledge sources.  

Agents can be configured in the system to address specific needs of the NOC. Each agent is powered by a Large Language Model (LLM) with function-calling capabilities, enabling it to invoke the right tools or knowledge bases based on the task description.  

In our scenario, we will build agents for **Network Status**, **Server Status**, **Incident Diagnosis**, and **Communications**, all coordinated by a **Supervisor Agent**. This setup allows the NOC Supervisor to ask questions in plain language, such as checking server health, investigating site-specific outages, diagnosing root causes, and drafting updates for field teams.  

There is an argument to be made that a truly agentic solution would demonstrate a high degree of autonomy. In such a setup, the system itself could monitor alerts, analyze logs, determine the root cause, generate a remediation plan, and notify stakeholders — all without human intervention. However, we can also maintain a **“human in the loop”** approach, where the NOC Supervisor drives the workflow step by step, verifying outputs from each agent before proceeding to the next stage. This flexibility allows organizations to balance automation with oversight.  

<div style="border: 2px solid black; padding: 10px;">
Even though we will take you through a complete and working example, you should also consider making changes that fit your desired use case, and only take this description as a reference point that guides you along your own implementation.
</div>  

### Pre-requisites  

- Check with your instructor to make sure **all systems** are up and running before you continue.  
- If you're an instructor running this lab, check the **Instructor's guides** to set up all environments and systems.  
