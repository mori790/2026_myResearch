# Slide 1 — Title

Good afternoon everyone.

Today, I will report what I learned about the theoretical foundations of Byzantine Fault Tolerance.

I studied *The Byzantine Generals Problem* because I wanted to understand PBFT more deeply, especially why PBFT requires (3f+1) replicas and multiple communication phases.

This presentation is therefore not a detailed paper summary. Instead, I will focus on the concepts that I understood and how they connect to PBFT.

---

# Slide 2 — What I Studied This Week

This week, I studied the theoretical background of Byzantine Fault Tolerance.

I reviewed the difference between crash faults and Byzantine faults, and I read *The Byzantine Generals Problem*.

I learned why three nodes cannot tolerate one Byzantine fault and understood the intuition behind the (3f+1) requirement.

This gave me a stronger foundation for studying PBFT.


---

# Slide 3 — My Understanding of Fault Models

First, I clarified the difference between crash faults and Byzantine faults.

In a crash fault, a node simply stops responding. Because the node becomes silent, its failure is relatively easy to observe.

Paxos and Raft mainly consider this type of failure.

In contrast, a Byzantine node can send incorrect messages.

For example, it may send value X to one node and value Y to another node.

This makes Byzantine faults much harder to handle.
---

# Slide 4 — The Core Problem I Understood

The central problem is that correct nodes may observe conflict values.

As I mentioned, the faulty node sends value X to Node B and value Y to Node C.

As a result, B and C receive conflicting information.

The important point is that Byzantine Fault Tolerance is not mainly about identifying which node is faulty.

The real objective is to guarantee that correct nodes still make the same decision, even when they receive inconsistent information.

---

# Slide 5 — My Understanding of the (3f+1) Requirement

From this impossibility result, I understood the meaning of the (3f+1) requirement.

To tolerate one Byzantine fault, four nodes are required.

To tolerate two Byzantine faults, seven nodes are required.

The important realization is that this requirement is not an arbitrary engineering choice made by PBFT.

It comes from a fundamental limitation of Byzantine agreement.

Correct nodes need enough independent reports so that faulty nodes cannot create two conflicting but apparently valid views.

---

# Slide 6 — Why 3 nodes are not enough, But 4 nodes are

With three nodes, one Byzantine node can create conflicting views that correct nodes cannot distinguish.

With four nodes, the correct nodes can compare enough independent reports to overcome one faulty node.

Therefore, tolerating one Byzantine fault requires at least four nodes, which is the basis of the (3f+1) rule.


---

# Slide 7 — What I Understand Now

At this point, I understand that Byzantine faults are fundamentally stronger than crash faults.

I also understand that the main objective is agreement among correct nodes, rather than identifying the faulty node.

The (3f+1) requirement exists because correct nodes need enough overlapping support to prevent conflicting decisions.

Finally, I understand the basic intuition behind PBFT.

Replicas do not trust the leader alone.

They exchange proposals, require enough matching messages, and try to preserve safety even when some replicas behave arbitrarily.

---

# Slide 8 — Next Steps

My next step is to read *Practical Byzantine Fault Tolerance*.

I will first focus on the system model and the normal-case protocol.

Then, I plan to trace one request using four replicas with (f=1).

After that, I would like to implement a small PBFT simulator so that I can observe normal execution and Byzantine failure scenarios.

Finally, I will compare PBFT with Paxos, Raft, and HotStuff to clarify the differences in fault models, quorums, and communication patterns.

---

# Slide 9 — Takeaway

To conclude, Byzantine Fault Tolerance is about creating a consistent shared decision even when some nodes provide conflicting information.

By reading *The Byzantine Generals Problem*, I gained the theoretical basis needed to understand why PBFT requires (3f+1) replicas and why replicas must communicate in multiple phases.

This gives me a stronger foundation for studying the actual PBFT protocol next.

Thank you for listening.
