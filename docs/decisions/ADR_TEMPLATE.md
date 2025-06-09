# Architecture Decision Record Template

**ADR-[NUMBER]:** [Short title of solved problem]  
**Date:** [YYYY-MM-DD]  
**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]  
**Deciders:** [List of people involved in decision]

## Context

What is the issue that we're seeing that is motivating this decision or change? Provide enough context so that someone unfamiliar with the project can understand the problem.

## Decision Drivers

* [Driver 1: e.g., We need to support 10,000+ books]
* [Driver 2: e.g., Must work within Calibre's Qt environment]
* [Driver 3: e.g., Cannot use NumPy due to Calibre restrictions]

## Considered Options

### Option 1: [Option name]
* **Pros:**
  * [Advantage 1]
  * [Advantage 2]
* **Cons:**
  * [Disadvantage 1]
  * [Disadvantage 2]

### Option 2: [Option name]
* **Pros:**
  * [Advantage 1]
  * [Advantage 2]
* **Cons:**
  * [Disadvantage 1]
  * [Disadvantage 2]

### Option 3: [Option name]
* **Pros:**
  * [Advantage 1]
  * [Advantage 2]
* **Cons:**
  * [Disadvantage 1]
  * [Disadvantage 2]

## Decision

We will go with **Option [X]** because [justification].

### Implementation Details
```python
# Example code showing the pattern
class Example:
    pass
```

## Consequences

### Positive
* [Positive consequence 1]
* [Positive consequence 2]

### Negative
* [Negative consequence 1]
* [Negative consequence 2]

### Risks
* [Risk 1 and mitigation strategy]
* [Risk 2 and mitigation strategy]

## Links

* [Link to relevant documentation]
* [Link to related ADRs]
* [Link to implementation PR]

---

## Notes for ADR Authors

1. **Keep it brief** - ADRs should be 1-2 pages max
2. **Focus on the "why"** - The decision rationale is more important than implementation details
3. **Be honest about trade-offs** - Every decision has downsides
4. **Reference related decisions** - Link to other ADRs that influenced or are influenced by this decision
5. **Update status** - Mark as Deprecated or Superseded when decisions change