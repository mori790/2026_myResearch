# Weekly Research Progress — Speaker Script

## Slide 1: Title
My current research direction is Byzantine fault tolerance in Kubernetes control planes.

This week, I mainly worked on narrowing the scope of my poster project, understanding the basic Kubernetes control-plane architecture, and investigating related work.

---

## Slide 2: Research Direction

My current research focus is Kubernetes from a distributed systems perspective.

My short-term goal is to prepare a poster presentation in five weeks.

For this poster, I will focus on understanding how different control-plane failures affect Kubernetes.

The main research question is:

How do crash failures and selective communication failures differently affect Kubernetes control-plane availability and convergence?

The diagram shows the relationship between the current poster project and my future research.

The poster project focuses on failure characterization.

After that, I plan to investigate possible solutions such as PBFT, HotStuff, and verifiable logs.

---

## Slide 3: Why This Topic?

Kubernetes strongly depends on its control plane to manage the entire cluster.

The API server receives requests from users and other Kubernetes components.

etcd stores important cluster data, including Deployments, ConfigMaps, Pods, and other desired-state information.

Controllers and the scheduler use this information to manage the cluster.

Standard etcd uses Raft.

Raft is mainly designed to tolerate crash failures, such as a node or process completely stopping.

However, a faulty component may remain active while behaving abnormally.

For example, it may delay messages, drop only some messages, or communicate with only part of the cluster.

Such behavior may be more difficult to detect than a complete crash.

Therefore, I want to investigate how these failures affect Kubernetes.

---

## Slide 4: What I Learned This Week

The most important thing I learned this week is that Kubernetes is a distributed control-loop system.

When a user executes a command with kubectl, kubectl does not directly create a Pod on a worker node.

First, the request is sent to the API server.

The desired state is then stored in etcd.

Controllers observe the current and desired states and try to reduce the difference between them.

The scheduler decides which worker node should execute each Pod.

Finally, the kubelet on the selected worker node starts the container.

This means that many components must cooperate correctly to realize the desired state.

A failure in etcd or in control-plane communication may interrupt this process.

---

## Slide 5: Deployment Creation Flow

This diagram shows the flow of creating a Deployment.

The important idea is that Kubernetes stores a desired state rather than executing only a one-time command.

For example, when the desired number of replicas is three, Kubernetes continuously tries to maintain three Pods.

If one Pod disappears, the controller creates another Pod.

Therefore, incorrect or unavailable state in the control plane may prevent Kubernetes from converging to the desired state.

---

## Slide 6: Scope of the Poster Project

Because I have only five weeks, I narrowed the scope of the poster project.

The main target components are etcd, the API server, and communication between control-plane components.

The failure scenarios include an etcd follower crash, an etcd leader crash, network delay, and selective network partition.

The Kubernetes operations used in the experiments will include Deployment creation, Deployment scaling, and ConfigMap updates.

For this poster, I will not implement PBFT or HotStuff.

I will also not study worker-node Byzantine failures, large-scale clusters, or arbitrary false responses from malicious replicas.

The purpose of this limited scope is to identify which failure behaviors have an important effect on Kubernetes before implementing a more complex BFT solution.

---

## Slide 7: Reference Paper

The main related paper I use is this work by Diouf, Elbiaze, and Jaafar.

It studies Byzantine fault tolerance in multi-master Kubernetes clusters.

This paper gives me the starting point for understanding how BFT can be connected to Kubernetes control planes.

---

## Slide 8: Related Work Positioning — KmMR

The most important related work I found is KmMR.

KmMR studies Byzantine fault tolerance in multi-master Kubernetes clusters.

This paper's main conclusion is that you can handle not only a crash failure but also Byzantine failure by changing kubernetes' replication method from Raft to BFT SMaRt.

It integrates BFT-SMaRt into Kubernetes and proposes a system that can tolerate Byzantine failures.

KmMR focuses on building and evaluating a BFT-based solution.

My current work has a different goal.

I will first use standard Kubernetes and inject different failure conditions.

Then, I will observe how those failures affect availability, latency, recovery, and convergence.

Therefore, my work is positioned as a preparatory step toward future BFT integration.

The results should help me identify whether PBFT, HotStuff, or another mechanism is appropriate for Kubernetes.

---

## Slide 9: Planned Fault Scenarios

I currently plan to evaluate five scenarios.

F0 is normal operation.

This provides the baseline performance for comparison.

F1 is an etcd follower crash.

In this scenario, I will examine whether the cluster continues operating correctly when one non-leader replica stops.

F2 is an etcd leader crash.

I will measure how long it takes to elect a new leader and restore normal operation.

F3 is network delay.

I will add delays to communication involving an etcd replica and observe the effect on API latency and state convergence.

F4 is selective network partition.

In this case, a replica does not fully stop, but it can communicate with only part of the cluster.

This scenario is closer to abnormal behavior than a simple crash.

However, I will describe it as a Byzantine-like or selective communication failure rather than a complete Byzantine fault.

---

## Slide 10: Evaluation Metrics

Following the example set by the paper, we will evaluate it as follows:

This evaluation metrics are slightly difference from original paper.

Original paper focuses on the difference between two protocol Raft and BFT-SMaRt.

On the other hand, I focuses on more concreate effect from users perspective.

---

## Slide 11: Five-Week Plan

This slide shows my five-week research schedule.

In the first week, I fixed the research scope, studied the control-plane operation flow, and started investigating KmMR.

I will also prepare the experimental environment.

In the second week, I will measure normal baseline performance and perform crash-fault experiments.

In the third week, I will perform network-delay and selective communication-failure experiments.

In the fourth week, I will analyze the results.

I will also consider how the observed problems relate to PBFT, HotStuff, or other possible solutions.

In the fifth week, I will finalize the poster, figures, results, and presentation story.

The main progress this week was defining a realistic scope and understanding how Kubernetes control-plane components cooperate.

---

## Slide 12: Takeaways

To conclude, I learned that Kubernetes is a desired-state distributed control system.

etcd is a central component because it stores the cluster state used by the API server, controllers, and scheduler.

I also learned that crash failures and selective communication abnormalities should be considered separately.

A complete crash is relatively easy to detect.

However, a component that remains active while delaying or selectively dropping messages may create more complex problems.

Before introducing PBFT or HotStuff, I first need to understand which failures actually affect Kubernetes and how they affect it.

This poster project will provide the experimental foundation for my future research on Byzantine fault tolerance in Kubernetes control planes.

Thank you for listening.
