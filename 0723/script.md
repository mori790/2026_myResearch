## Slide 1 — Title

Today, I'd like to introduce the paper *Can AI Agents Agree?*

Instead of summarizing the entire paper, I'll focus on how it differs from PBFT and how it relates to my research direction.

---

## Slide 2 — Research Motivation

My goal is to compare consensus in classical distributed systems with consensus among LLM agents.

I want to identify which assumptions of PBFT no longer hold when the nodes are AI agents.

---

## Slide 3 — PBFT vs. LLM Agent Consensus

The biggest difference is the node model.

PBFT assumes deterministic nodes that always follow the protocol.

In contrast, LLM agents interpret instructions through natural language, so their behavior is probabilistic.

Also, PBFT reaches agreement on system state, while this paper focuses on agreement on answers.

---

## Slide 4 — Where PBFT Assumptions Break

PBFT assumes that correct nodes always execute the protocol correctly.

However, LLM agents may hallucinate, misunderstand instructions, or forget context.

These behaviors are not necessarily malicious, but they can still break the protocol.

This suggests that AI-agent systems may require a new fault model beyond classical Byzantine faults.

---

## Slide 5 — Research Direction

This paper showed me that distributed systems with LLM agents are more difficult than I expected.

Because LLM agents are probabilistic, even honest agents may fail to execute consensus protocols correctly.

Also, defining failures and evaluating the system are still challenging.

Therefore, I decided to pause this direction and shift my focus to Kubernetes-based distributed systems.

My next step is to explore concrete research topics in Kubernetes.

