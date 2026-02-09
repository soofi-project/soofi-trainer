# Task

- user story: #US-05

/label ~UserStory_US-05
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**End-to-End Test**

Test the complete flow from user input to agent recommendation and document the results.

## Test Scenario

Based on the example conversation from the agent specification:

**User**: Wants to build a medical diagnosis support model based on patient symptoms and medical history. Has no own data. Data must be GDPR-compliant. Has an NVIDIA A100 40GB GPU available.

**Expected flow**:
1. User describes their use case via Open WebUI
2. Agent asks clarifying questions (domain, data situation, hardware, constraints)
3. Agent retrieves relevant knowledge about suitable methods from the knowledge base
4. Agent searches for public datasets on HuggingFace and/or Eclipse Dataspace (GDPR-compliant, medical domain)
5. Agent applies decision logic and recommends a method (e.g. QLoRA)
6. Agent generates a structured recommendation report with alternatives and next steps

## Checkpoints

- [ ] All services start successfully via `./up.sh`
- [ ] Weaviate is healthy and knowledge is ingested
- [ ] Vector MCP is healthy
- [ ] Knowledge is searchable (test via MCP Inspector)
- [ ] Agent conducts structured interview in German
- [ ] Agent retrieves relevant knowledge and cites sources
- [ ] Agent provides recommendation with reasoning, alternatives, and next steps
- [ ] All services stop cleanly via `./down.sh`

## Documentation Checklist

- [ ] README explains setup and usage
- [ ] Architecture diagram is accurate
- [ ] All service URLs documented
- [ ] Troubleshooting section exists

# Branches

- feature/US-05-integration
