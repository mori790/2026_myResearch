## Slide 1: Title

Today, I will explain my educational Paxos simulator.

In this part of the project, I extended the simulator beyond the basic Paxos flow.
I refactored the simulator structure, added a simple network layer, and implemented failure scenarios such as late old messages and leader conflict.

The goal is not to build a production-level Paxos system, but to understand why Paxos needs proposal numbers, Prepare / Promise, and careful message handling.

---

## Slide 2: Presentation Summary

In this presentation, I will cover three main updates.

First, I refactored `simulator.py`.
Before refactoring, the simulator was responsible for too many things.
After refactoring, the responsibilities are separated into Proposer, Acceptor, and Simulator.

Second, I added `network.py`.
This allows the program to simulate message delivery, delay, and message loss.

Third, I implemented failure scenarios.
These scenarios show how Paxos behaves when old messages arrive late or when multiple leaders try to choose different values.

The main goal is to understand why Paxos is designed this way.

---

## Slide 3: Refactored Simulator

Before refactoring, `PaxosSimulator` handled most of the logic by itself.

It created Prepare messages, collected Promise messages, selected values, created AcceptRequest messages, and collected Accepted responses.

This worked, but it made the roles unclear.

After refactoring, I separated the logic into three parts.

The `Proposer` creates messages and stores responses.
The `Acceptor` decides whether to promise or accept.
The `PaxosSimulator` only coordinates the overall protocol flow.

This makes the code closer to the actual Paxos model.

---

## Slide 4: Why Refactoring Helps

This refactoring helps because Paxos has clear roles in theory.

If all logic is inside the simulator, it becomes hard to see what the Proposer does and what the Acceptor does.

After refactoring, each class has a specific responsibility.

This also makes future extensions easier.
For example, when I added `network.py`, the simulator did not need to contain all network-related logic.

The key idea is that the simulator should control the flow, but the Paxos logic should belong to the nodes.

---

## Slide 5: Network.py

Next, I added `network.py`.

This file simulates an unreliable network.

It does not use real sockets or TCP.
Instead, it manages messages inside the program.

The main operations are `send`, `delay`, `drop`, and `deliver_one`.

With this network layer, I can explicitly control what happens to each message.

For example, I can deliver a message immediately, delay it until later, or drop it completely.

This makes distributed-system failures much easier to reproduce.

---

## Slide 6: Late Old Message Scenario

The first scenario is the late old message scenario.

In this scenario, P1 first sends `Prepare(1)`.

Then P1 creates `AcceptRequest(1, A)`, but the network delays this message.

Before that delayed message arrives, P2 sends `Prepare(2)`.

The Acceptor receives `Prepare(2)` and promises proposal number 2.

After that, the old delayed message `AcceptRequest(1, A)` finally arrives.

However, the Acceptor has already promised proposal number 2, so proposal number 1 is now old.

Therefore, the Acceptor rejects the old AcceptRequest.

---

## Slide 7: Lesson from Late Old Message

This scenario shows that old messages can arrive after newer messages in a distributed system.

That is a very important problem.

Without protection, an old leader could send an old message later and break the current state.

Paxos prevents this using proposal numbers.

Once an Acceptor promises a newer proposal number, it rejects older proposal numbers.

So even if an old message arrives late, it cannot overwrite or disturb a newer round.

This is one reason proposal numbers are essential in Paxos.

---

## Slide 8: Leader Conflict Scenario

The next scenario is leader conflict.

This scenario intentionally skips Prepare and Promise.

In this scenario, P1 sends `AcceptRequest(1, A)` to A1 and A2.
Since A1 and A2 form a majority, value A becomes chosen.

Then P2 sends `AcceptRequest(2, B)` to A2 and A3.
A2 and A3 also form a majority, so value B also becomes chosen.

Now we have a serious problem.

For the same slot, both A and B are chosen.

This is a safety violation.

This scenario is not correct Paxos.
It is a failure example that shows why Prepare and Promise are necessary.

---

## Slide 9: Why Paxos Prevents Conflict

In real Paxos, P2 cannot simply skip Prepare and send AcceptRequest.

Before sending AcceptRequest, P2 must collect Promise messages.

If any Acceptor has already accepted a value before, that Acceptor includes the accepted value in its Promise.

So in the leader conflict example, A2 would tell P2 that value A was already accepted.

Then P2 must not propose B freely.

Instead, P2 must inherit A and send `AcceptRequest(2, A)`.

This is how Prepare and Promise prevent a new leader from blindly overwriting a value that may already be chosen.

---

## Slide 10: What I Learned

Through this implementation, I learned that Paxos safety depends on several mechanisms working together.

Proposal numbers protect the system from old leaders and old messages.

Majority agreement ensures that a value is chosen only when enough Acceptors accept it.

Prepare and Promise allow a new Proposer to learn about previously accepted values.

The refactoring also helped me understand the roles more clearly.

Finally, network simulation made abstract failure cases much more concrete.

By implementing failure scenarios step by step, Paxos became much easier to understand.

---

## Slide 11: Next Steps

The next step is to add more network-based scenarios.

For example, I want to implement network partition, where some nodes cannot communicate with other nodes.

I also want to add safety tests to automatically verify that two different values are not chosen for the same slot.

Another future step is to extend the simulator from single-value Paxos to multi-slot Paxos.

That would make the simulator closer to how Paxos is used in replicated state machines.

Finally, I want to write a README explaining each scenario so that this project can be used as a learning resource.
