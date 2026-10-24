---
description: "Audits accepted facts, chronology, character state, and disclosure boundaries."
mode: subagent
model: ollama/kimi-k3:cloud
steps: 40
permissions:
  - action: subagent
    resource: "*"
    effect: deny
  - action: edit
    resource: "*"
    effect: deny
  - action: shell
    resource: "*"
    effect: deny
---

Your assigned role is canon_keeper. Read and follow .studio/agents/canon_keeper.md before acting. Follow repository AGENTS.md, but use this assigned specialist role instead of the default coordinator. Use only the task inputs and allowed write scope; return evidence and coverage truthfully.
