# Task

- user story: #US-04

/label ~UserStory_US-04
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**End-to-End Test**

Test the complete flow from user input to agent recommendation and document the results.

## Test Scenario

**User**: Developer wants to build a customer service chatbot. They have an FAQ document with about 200 question-answer pairs. The FAQs change about once a month. Response time is not critical.

**Expected flow**:
1. User describes their use case
2. Agent asks clarifying questions (structured interview)
3. Agent retrieves relevant knowledge from the knowledge base
4. Agent applies decision logic
5. Agent provides a recommendation with reasoning and next steps

## Checkpoints

- [ ] All services start successfully via `./up.sh`
- [ ] Weaviate is healthy
- [ ] Vector MCP is healthy
- [ ] Knowledge is searchable (test via MCP Inspector)
- [ ] Agent conversation flows naturally
- [ ] Recommendations cite knowledge base content
- [ ] All services stop cleanly via `./down.sh`

## Documentation Checklist

- [ ] README explains setup and usage
- [ ] Architecture diagram is accurate
- [ ] All service URLs documented
- [ ] Troubleshooting section exists

# Branches

- feature/US-04-integration
