## Slide 1 — Title

Today, I will introduce the paper *Can AI Agents Agree?*

Rather than explaining every detail of the paper, I will focus on one specific question: how consensus among LLM agents differs from consensus in PBFT.

I think this comparison is important because PBFT assumes that correct nodes execute a predefined protocol faithfully. However, LLM agents interpret instructions through natural language and probabilistic reasoning.

By comparing these two settings, I would like to identify what new problems arise when consensus protocols are applied to AI agents.

---

## Slide 2 — Research Motivation

The main question of this presentation is whether LLM agents can reliably reach consensus in the same way as nodes in a traditional distributed system.

In classical distributed systems, consensus protocols are designed under clearly defined assumptions about nodes, communication, and failures.

However, LLM agents are not ordinary deterministic processes. They may misunderstand instructions, generate incorrect information, or behave differently even when they receive the same prompt.

Therefore, my goal is not simply to ask whether LLM agents can agree.

Instead, I want to examine which assumptions of PBFT no longer hold when the participating nodes are LLM agents.

This comparison may help us identify new research problems at the intersection of distributed systems and AI-agent systems.

---

## Slide 3 — PBFT vs. LLM Agent Consensus

The most important difference between PBFT and this paper is the node model.

In PBFT, each correct node is a deterministic process. When it receives a valid message in a particular state, it performs a predefined state transition and sends the corresponding messages.

Therefore, a correct node always follows the protocol exactly.

In contrast, the nodes in this paper are LLM agents. They receive protocol instructions in natural language, interpret them, reason about the current situation, and then produce a response.

This means that protocol execution itself becomes probabilistic.

Even an honest agent may send an incorrect message because it misunderstood the prompt or made a reasoning error.

There is also a difference in the consensus target.

PBFT usually reaches agreement on a request, operation order, or replicated state.

In this paper, agents mainly try to agree on an answer, such as a numerical value.

Therefore, both the participating nodes and the object of consensus are different from those in PBFT.

---

## Slide 4 — Where PBFT Assumptions Break

PBFT assumes that all correct nodes understand incoming messages correctly and execute the protocol faithfully.

The Byzantine fault model allows faulty nodes to behave arbitrarily, but all non-faulty nodes are still assumed to be reliable protocol executors.

This assumption becomes difficult to maintain for LLM agents.

For example, an LLM agent may hallucinate a message that was never received.

It may forget information from an earlier round because of context limitations.

It may misunderstand the meaning of a quorum or incorrectly count the number of votes.

It may also produce different decisions across repeated executions because its reasoning is non-deterministic.

These behaviors are not necessarily malicious.

However, from the perspective of the protocol, they may look similar to Byzantine behavior because the agent can produce arbitrary or inconsistent messages.

This creates an important question: should these failures be treated as Byzantine faults, or should we define a separate fault model for probabilistic reasoning errors?

I think this distinction will be important for future research.

---

## Slide 5 — Possible Research Direction and Takeaways

The paper mainly considers consensus on an answer.

For example, multiple agents discuss a numerical problem and attempt to agree on one final value.

My possible research direction is to extend the consensus target from an answer to a workflow state.

In a multi-agent workflow, different agents may perform different roles, such as research, planning, coding, and reviewing.

In this setting, the important question is not always whether all agents produce the same answer.

Instead, we may need to decide whether a particular stage has been completed correctly and whether the system can safely proceed to the next stage.

For example, has the research stage collected sufficient and reliable evidence?

Is the generated code ready to be reviewed?

Can the workflow proceed even if one agent provides incorrect or misleading information?

I currently call this idea workflow consensus under semantic Byzantine faults.

The main takeaway is that PBFT and LLM-agent consensus have fundamentally different assumptions.

LLM agents are probabilistic protocol executors, and even honest agents may fail to follow the protocol correctly.

Existing work mainly studies agreement on answers, while reliable agreement on workflow transitions appears to be less explored.

My next step is to examine the paper’s system model, failure model, and experimental results in more detail, and then compare them formally with PBFT.
