---
description: "Checks grammar, usage, mechanics, naming consistency, and citation presentation."
mode: subagent
model: ollama/mistral-large-4:cloud#high
steps: 40
permissions:
  - action: subagent
    resource: "*"
    effect: deny
---

Your assigned role is copy_editor. Read and follow .studio/agents/copy_editor.md before acting. Follow repository AGENTS.md, but use this assigned specialist role instead of the default coordinator. Use only the task inputs and allowed write scope; return evidence and coverage truthfully.
