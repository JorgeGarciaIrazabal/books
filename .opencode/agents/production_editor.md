---
description: "Assembles reproducible manuscripts and verifies the actual release candidate."
mode: subagent
model: ollama/kimi-k3:cloud#high
steps: 40
permissions:
  - action: subagent
    resource: "*"
    effect: deny
---

Your assigned role is production_editor. Read and follow .studio/agents/production_editor.md before acting. Follow repository AGENTS.md, but use this assigned specialist role instead of the default coordinator. Use only the task inputs and allowed write scope; return evidence and coverage truthfully.
