# Slide 1 — Title

Good afternoon everyone.

Today, I will introduce *The Byzantine Generals Problem*, which was proposed by Lamport, Shostak, and Pease in 1982.

This paper is one of the most influential works in distributed systems because it established the theoretical foundation for Byzantine Fault Tolerance.

I will explain the motivation, the problem setting, the OM algorithm, and finally how this work connects to PBFT.

---

# Slide 2 — Overview

This presentation consists of six parts.

First, I will explain why Byzantine faults are more difficult than crash faults.

Next, I will introduce the Byzantine Generals Problem and the concept of Interactive Consistency.

Then, I will explain why three generals cannot solve the problem.

After that, I will introduce the OM algorithm and explain why at least (3m+1) generals are required.

Finally, I will discuss how these ideas led to PBFT.

---

# Slide 3 — Crash Fault vs Byzantine Fault

Before introducing the paper, let's compare two fault models.

On the left is a crash fault. In this model, a node simply stops responding. This is the fault model assumed by protocols such as Paxos and Raft.

On the right is a Byzantine fault. Here, a faulty node may send different messages to different nodes. It can lie, behave arbitrarily, or even act maliciously.

Byzantine faults are much more difficult to handle because the faulty node is still communicating.

---

# Slide 4 — Byzantine Generals Problem

The paper explains the problem using a military example.

There is one commander and several lieutenants surrounding a city.

They must all make the same decision: either attack or retreat.

If loyal generals choose different actions, they will lose the battle.

Therefore, the goal is for all loyal generals to reach the same decision, even if some generals are traitors.

---

# Slide 5 — Interactive Consistency

The paper defines correctness using two conditions called Interactive Consistency.

The first condition, IC1, requires that all loyal lieutenants obey the same order.

The second condition, IC2, states that if the commander is loyal, every loyal lieutenant must follow the commander's order.

These two conditions become the formal definition of correctness throughout the paper.

---

# Slide 6 — Why Three Generals Are Impossible

Now let's see why three generals are not enough.

Suppose the commander is malicious.

The commander sends "Attack" to one lieutenant and "Retreat" to the other.

The two lieutenants exchange their observations, but each lieutenant sees the same situation.

One possibility is that the commander is lying. Another possibility is that the other lieutenant is lying.

From their local information alone, they cannot distinguish these two worlds.

Therefore, no deterministic algorithm can satisfy both IC1 and IC2.

---

# Slide 7 — Information Ambiguity

This table illustrates the key idea of the impossibility proof.

In two different worlds, Lieutenant B observes exactly the same information.

However, the actual traitor is different.

Since B cannot distinguish between these two worlds, any decision rule will fail in at least one of them.

This is an information-theoretic impossibility result.

The problem is not identifying the traitor. The real problem is that loyal nodes do not have enough information to make a correct decision.

---

# Slide 8 — Why (3m+1)?

The paper proves that to tolerate up to (m) Byzantine traitors, at least (3m+1) generals are required.

For example, tolerating one traitor requires four generals, while tolerating two traitors requires seven generals.

This formula is not specific to PBFT. It was first established in this paper and later became the theoretical foundation of Byzantine fault-tolerant consensus protocols.

---

# Slide 9 — OM(0)

The authors then introduce the Oral Messages algorithm, or OM.

OM(0) assumes there are no traitors.

The commander simply sends a value to every lieutenant, and each lieutenant adopts that value.

Since there are no Byzantine faults, message forwarding is unnecessary.

---

# Slide 10 — OM(1)

OM(1) tolerates one Byzantine traitor.

First, the commander sends an order to every lieutenant.

Then, each lieutenant forwards the received order to every other lieutenant.

Finally, every lieutenant performs majority voting.

The key idea is to verify information through multiple communication paths instead of trusting the commander alone.

---

# Slide 11 — Example of OM(1)

This slide shows an example where the commander is malicious.

The commander sends inconsistent orders to different lieutenants.

However, the loyal lieutenants exchange what they received.

After collecting all reports, they perform majority voting.

As a result, every loyal lieutenant reaches the same decision.

The commander may lie, but loyal nodes can still agree.

---

# Slide 12 — General Form of OM(m)

OM(m) is defined recursively.

Each lieutenant behaves like a commander and runs OM(m−1).

Therefore, OM(2) calls OM(1), and OM(1) calls OM(0).

This recursive structure enables the protocol to tolerate increasingly more Byzantine faults.

---

# Slide 13 — Message Depth

One interesting observation is that deeper recursion is needed to tolerate more traitors.

OM(0) requires one communication step.

OM(1) requires two steps.

OM(2) requires three steps.

In general, tolerating more Byzantine faults requires more communication.

---

# Slide 14 — Connection to PBFT

Finally, let's connect this paper to PBFT.

The Byzantine Generals Problem established the theoretical limits of Byzantine agreement.

It introduced the OM algorithm and proved the (3m+1) requirement.

PBFT builds directly on these results.

Instead of recursive oral messages, PBFT introduces practical phases such as Pre-prepare, Prepare, Commit, and View Change to implement Byzantine fault-tolerant replication efficiently.

---

# Slide 15 — Takeaways

To summarize,

Byzantine faults are much more challenging than crash faults because faulty nodes can send conflicting messages.

The paper formalized correctness using Interactive Consistency.

It proved that three generals cannot solve the problem when one may be a traitor.

It also introduced the OM algorithm and established the famous (3m+1) requirement.

Finally, these theoretical results became the foundation of PBFT and many modern Byzantine fault-tolerant consensus protocols.

Thank you for listening.
