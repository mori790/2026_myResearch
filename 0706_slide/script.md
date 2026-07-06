## Slide 1: Presentation Overview

Today, I will explain two parts of my recent progress.

First, I will talk about my educational Paxos simulator.
In this part, I refactored the simulator, added a simple network layer, and implemented failure scenarios.

Second, I will explain my current research direction after reviewing recent RAG papers.

The main goal of this presentation is to connect my implementation practice with my broader research interest in distributed systems.

---

## Slide 2: Part 1: Educational Paxos Simulator

First, I will explain my educational Paxos simulator.

I extended the simulator beyond the basic Paxos flow.

The goal is not to build a production-level Paxos system.
Instead, the goal is to understand why Paxos needs proposal numbers, Prepare and Promise messages, majority agreement, and careful message handling.

Paxos is difficult to understand only from theory, so I tried to make the behavior of the protocol visible through code.

In particular, I focused on failure scenarios, because failures make the role of each Paxos mechanism much clearer.

---

## Slide 3: Paxos Simulator: Main Updates

I made three main updates to the simulator.

First, I refactored `simulator.py`.

Second, I added `network.py`.

Third, I implemented failure scenarios.

Before these updates, the simulator could show the basic Paxos flow.
However, it was still difficult to understand how Paxos behaves when messages are delayed or when leaders conflict.

So the main goal of these updates was to observe why Paxos is designed this way under failure scenarios.

---

## Slide 4: Refactored Simulator

Before refactoring, `PaxosSimulator` handled most of the logic by itself.

It created Prepare messages, collected Promise messages, selected values, created AcceptRequest messages, and collected Accepted responses.

This implementation worked, but it made the roles unclear.

After refactoring, I separated the logic into three parts.

The `Proposer` creates messages and stores responses.

The `Acceptor` decides whether to promise or accept.

The `PaxosSimulator` coordinates the overall protocol flow.

This structure makes the code closer to the actual Paxos model.

---

## Slide 5: Why Refactoring Helps

This refactoring helped because Paxos has clear roles in theory.

If all logic is inside the simulator, it becomes hard to see what each node is responsible for.

After refactoring, each class has a specific responsibility.
This makes the code easier to read and easier to extend.

For example, when I added `network.py`, the simulator did not need to contain all network-related logic.

The key idea is that the simulator should control the overall flow, but the Paxos logic should belong to the nodes.

---

## Slide 6: Network Layer

Next, I added `network.py`.

This file simulates an unreliable network.

It does not use real sockets or TCP.
Instead, it manages messages inside the program.

The main operations are `send`, `delay`, `drop`, and `deliver_one`.

With this network layer, I can explicitly control message delivery, delay, and loss.

For example, I can deliver a message immediately, delay it until later, or drop it completely.

This makes distributed-system failures much easier to reproduce in the simulator.

---

## Slide 7: Leader Conflict Scenario

Next, I implemented a leader conflict scenario.

This scenario intentionally skips Prepare and Promise.
So this is not correct Paxos.
It is a failure example to show why Prepare and Promise are necessary.

In this scenario, P1 sends `AcceptRequest(1, A)` to A1 and A2.

Since A1 and A2 form a majority, value A becomes chosen.

Then P2 sends `AcceptRequest(2, B)` to A2 and A3.

A2 and A3 also form a majority, so value B also becomes chosen.

Now two different values are chosen for the same slot.

This is a serious safety violation.

---

## Slide 8: Why Paxos Prevents Leader Conflict

In real Paxos, P2 cannot simply skip Prepare and send AcceptRequest.

Before sending AcceptRequest, P2 must collect Promise messages from a majority of Acceptors.

If an Acceptor has already accepted a value, it includes that value in its Promise.

In the leader conflict example, A2 would tell P2 that value A was already accepted.

Therefore, P2 must not freely propose B.

Instead, P2 must inherit A and send `AcceptRequest(2, A)`.

This is how Prepare and Promise prevent a new leader from blindly overwriting a value that may already be chosen.

---

## Slide 9: What I Learned from the Simulator

Through this implementation, I learned that Paxos safety depends on several mechanisms working together.

Proposal numbers protect the system from old leaders and old messages.

Majority agreement ensures that a value is chosen only when enough Acceptors accept it.

Prepare and Promise allow a new Proposer to learn about previously accepted values.

Refactoring also helped me understand the roles more clearly.

Finally, network simulation made abstract failure cases much more concrete.

By implementing these scenarios, Paxos became easier to understand as an actual distributed protocol, not just as an abstract algorithm.

---

## Slide 10: Part 2: Why I Am Interested in RAG

Next, I will explain my current research direction.

I became interested in Retrieval-Augmented Generation, or RAG, through my previous university research.

In that work, I studied how external knowledge can be used to improve the reliability of LLM outputs.

However, RAG is not only an AI problem.

RAG connects language models with documents, databases, search indexes, and retrieval pipelines.

Because of that, RAG also has data management and system reliability problems.

My motivation is to study RAG from a distributed systems perspective.

---

## Slide 11: Main Question

My main research question is:

How can we make RAG systems reliable when the knowledge base is dynamically updated?

In real systems, documents are not static.

Documents can be added, updated, or deleted.

These changes must be reflected in many parts of the RAG pipeline.

For example, they must be reflected in chunks, embeddings, vector indexes, retrieved contexts, and citations.

If this propagation is incomplete, the LLM may generate answers based on stale or deleted information.

So I want to study how to guarantee reliability in this dynamic setting.

---

## Slide 12: Review Paper

To understand the research landscape, I reviewed a paper titled:

“Security and Privacy in Retrieval-Augmented Generation: Architectures, Threats, Defenses, and Future Directions for Building Trustworthy Systems.”

This review paper surveys security and privacy issues in RAG systems.

It shows that RAG introduces risks not only in the LLM itself, but also in retrieval, indexing, context construction, and generation.

This paper helped me understand that trustworthy RAG requires system-level design.

It also motivated me to focus on reliability issues inside the RAG pipeline, rather than only improving retrieval accuracy or prompting.

---

## Slide 13: Core Research Problem

The core research problem is that a RAG answer may be generated from outdated or inconsistent evidence.

RAG data changes form through multiple stages.

A document is split into chunks.

Chunks are converted into embeddings.

Embeddings are stored in a vector index.

The retriever selects relevant chunks.

Those chunks are placed into the context.

Finally, the LLM generates an answer.

The problem is that these stages may not be updated at the same time.

A document may be updated, but old chunks may remain.

Embeddings may be generated from outdated text.

Deleted documents may still exist in the vector index.

Citations may point to old document versions.

This can make the final answer unreliable.

---

## Slide 14: Why This Is a Distributed Systems Problem

This is a distributed systems problem because production RAG systems may use replicated or sharded vector indexes.

Updates and deletions must propagate across multiple components.

Queries may reach stale replicas or stale cached results.

Also, different parts of the RAG pipeline may observe different versions of the knowledge base.

For example, the retriever may use one version of the index, while the citation system may refer to another version of the document.

So the key issue is consistency.

My research direction is to study consistency guarantees for dynamic RAG systems.

In particular, I want to focus on freshness, deletion guarantees, and snapshot consistency.

---

## Slide 15: Overall Conclusion

To conclude, I worked on two connected directions.

First, through the Paxos simulator, I learned how distributed protocols preserve safety under message delay and leader conflict.

Second, through the RAG paper review, I found that RAG also has system-level reliability problems.

My current research interest is to connect these two directions.

I want to study RAG as a distributed data system, where versioning, freshness, deletion, and consistency must be guaranteed.

As the next step, I want to define these guarantees more clearly and investigate how to design a prototype system for dynamic RAG consistency.
