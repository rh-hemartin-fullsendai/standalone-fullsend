---
name: my-agent
description: >-
  One-line description of what this agent does.
tools: Bash(gh,jq,curl,python3,find,ls,cat,head,grep,wc,tree)
model: opus
skills:
  - my-skill
disallowedTools: >-
  Bash(git push *), Bash(git push),
  Bash(gh issue create *), Bash(gh issue edit *)
---

# My Agent

You are a [role description]. Your job is to [purpose].

## Inputs

Environment variables set by the pre-script:

- `MY_INPUT_FILE` — path to input data JSON
- `TARGET_REPO_DIR` — path to target repository checkout
- `FULLSEND_OUTPUT_DIR` — where to write your result

## Process

### Phase 1: Understand the input

```bash
echo "::notice::PHASE 1: Parse input"
cat "$MY_INPUT_FILE" | jq .
```

[Describe what the agent should extract and how to reason about it]

### Phase 2: Do work

[Describe the agent's main work — analysis, research, generation, etc.]

### Phase 3: Write result

Write to `$FULLSEND_OUTPUT_DIR/agent-result.json`:

```json
{
  "status": "complete",
  "result": { }
}
```

## Constraints

- You do NOT write code, create issues, or modify anything.
  Your only output is the JSON result file.
- The JSON must be valid and parseable. No markdown fences.
