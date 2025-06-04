Design the architecture for implementing: "$ARGUMENTS"

## Pre-Architecture Verification
1. **Confirm SPARC Analysis Exists**:
   - Has SPARC analysis been completed?
   - Is the chosen approach clear?
   - Are constraints understood?
   
   If NO: Run `/project:sparc-analyze $ARGUMENTS` first

2. **Gather Architectural Context**:
   ```bash
   # Analyze project structure
   find . -type f -name "*.py" | grep -E "(^|/)$ARGUMENTS" | sort
   
   # Find architectural patterns in use
   grep -r "class.*ABC\|@abstractmethod" --include="*.py" | head -10
   
   # Check existing design patterns
   grep -r "Singleton\|Factory\|Observer\|Strategy" --include="*.py" | head -10
   ```

## Architecture Design Process

### 1. Component Identification
**Identify Components Needed**:
```
┌─────────────────┐
│   Component A   │ Purpose: ...
├─────────────────┤ Responsibilities:
│ - method1()     │ - ...
│ - method2()     │ - ...
└─────────────────┘
        │
        ▼
┌─────────────────┐
│   Component B   │ Purpose: ...
├─────────────────┤ Responsibilities:
│ - method3()     │ - ...
└─────────────────┘
```

### 2. Interface Design
**Define Clear Contracts**:
```python
# Public API
class ComponentInterface(ABC):
    @abstractmethod
    def core_operation(self, param: Type) -> ReturnType:
        """What this does, why it exists"""
        pass
```

### 3. Data Flow Design
**Trace Data Through System**:
1. Input: [What format/type]
2. Transform: [What processing]
3. Store: [Where/how]
4. Retrieve: [When/why]
5. Output: [What format/type]

### 4. Integration Points
**Map Connections** (VERIFY THESE EXIST):
```python
# Where does this plug in?
existing_module.py:
  Line X: # New component integrates here
  Why: [Reason for this integration point]
```

### 5. Design Pattern Selection
**Choose Appropriate Patterns**:
- [ ] **Pattern**: [Factory/Strategy/Observer/etc]
  - Why needed: [Specific reason]
  - Where applied: [Component/module]
  - Example in codebase: [Show similar usage]

### 6. Error Handling Strategy
**Define Failure Modes**:
```python
# What can go wrong?
class SpecificError(Exception):
    """When does this occur"""
    
# How to handle?
try:
    risky_operation()
except SpecificError:
    # Recovery strategy
```

### 7. Testing Strategy
**Plan Testability**:
- **Unit testable**: [How to isolate components]
- **Mock points**: [What needs mocking]
- **Integration tests**: [What combinations]
- **Performance tests**: [What to measure]

### 8. Scalability Considerations
- **Data volume**: How does it handle 10x data?
- **Concurrency**: Thread-safe? Async-ready?
- **Memory**: What's the footprint?
- **Performance**: O(n) complexity analysis

## Architecture Validation

### 9. SOLID Principles Check
- [ ] **S**ingle Responsibility: Each class has one job
- [ ] **O**pen/Closed: Extensible without modification
- [ ] **L**iskov Substitution: Subclasses truly substitute
- [ ] **I**nterface Segregation: No fat interfaces
- [ ] **D**ependency Inversion: Depend on abstractions

### 10. Coupling Analysis
**Check Dependencies**:
```bash
# Find imports to assess coupling
grep -h "^import\|^from" $COMPONENT_FILES | sort | uniq -c
```
- High coupling risks: [List them]
- Mitigation strategies: [How to reduce]

### 11. Complexity Assessment
- **Cyclomatic complexity**: Keep methods under 10
- **Class complexity**: Keep classes under 200 lines
- **File complexity**: Keep files under 500 lines

## Architecture Documentation

### 12. Create Design Doc
```markdown
# Architecture: $ARGUMENTS

## Overview
[One paragraph summary]

## Components
[Component descriptions]

## Interactions
[Sequence or component diagram]

## Design Decisions
[Key choices and rationale]

## Risks
[What could go wrong]
```

## Verification Questions
Before proceeding to implementation:
1. Does this fit existing architecture?
2. Are all integration points real?
3. Is complexity justified?
4. Are there simpler alternatives?
5. Will this be maintainable?

## Next Steps
1. Get architecture review/feedback
2. Create detailed specifications: `/project:create-spec`
3. Write interface contracts first
4. Begin TDD implementation: `/project:tdd-cycle`

Remember: Good architecture makes implementation obvious.