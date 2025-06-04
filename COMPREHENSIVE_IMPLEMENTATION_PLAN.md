# Comprehensive Implementation Plan: Calibre Semantic Search v1.0

**Document Version**: 1.0  
**Created**: 2025-06-04  
**Scope**: Complete implementation addressing UI/Backend integration issues AND specification requirements  
**Methodology**: SPARC + TDD with Calibre-specific best practices

## 📋 Executive Summary

This plan addresses:
1. **Five critical UI/Backend integration issues** (see UI_BACKEND_INTEGRATION_DIAGNOSIS.md)
2. **Missing P0/P1 requirements** from calibre-semantic-spec-02.md
3. **Technical debt** from organic growth
4. **Architecture improvements** for maintainability

**Total Estimated Effort**: 20-25 hours  
**Recommended Team Size**: 1-2 developers  
**Critical Path**: Phase 0 → Phase 1 → Phase 2 (parallel possible after)

## 🎯 Success Criteria

1. All five integration issues resolved
2. P0 (Critical) requirements implemented:
   - Multi-provider support with fallback (FR-011)
   - Dimension auto-detection (FR-012)
   - At least hybrid chunking strategy (FR-013)
   - Complete index metadata (FR-010, FR-014)
3. Performance targets met (NFR-001, NFR-002)
4. Zero regression in existing functionality
5. 90%+ test coverage maintained

## 🔄 Git Flow Strategy

### Branch Structure
```
master
  ├── feature/fix-integration-phase-0  (Foundation fixes)
  ├── feature/fix-integration-phase-1  (Critical UI fixes)
  ├── feature/implement-requirements   (Spec requirements)
  └── feature/architecture-cleanup     (Technical debt)
```

### Commit Convention
```bash
# Format: <type>(<scope>): <subject>
# Types: fix, feat, refactor, test, docs, perf

fix(config): implement proper plugin reference passing
feat(chunking): add hybrid chunking strategy
test(integration): add service registry tests
docs(plan): update implementation progress
```

### PR Strategy
- One PR per phase (small, reviewable chunks)
- Each PR must pass all tests
- Update CHANGELOG.md in each PR
- Reference requirement IDs in commits

## 📚 Context Gathering Strategy

### Before Each Task
1. **Read existing code** - Use Read tool on all related files
2. **Search for patterns** - Use Grep/Glob for similar implementations
3. **Check tests** - Understand expected behavior
4. **Review Calibre docs** - Verify approach aligns with framework

### SPARC Analysis Template
```markdown
## Situation
- Current state: [describe]
- User impact: [describe]
- Technical debt: [describe]

## Problem
- Root cause: [identify]
- Symptoms: [list]
- Dependencies: [map]

## Analysis
- Options considered: [list]
- Trade-offs: [evaluate]
- Risks: [assess]

## Recommendation
- Approach: [decide]
- Justification: [explain]
- Success metrics: [define]

## Concerns
- Assumptions: [document]
- Unknowns: [list]
- Backup plans: [reference BACKUP_PLANS.md]
```

## 🏗️ Implementation Phases

### Phase 0: Foundation & Validation (2-3 hours)

**Purpose**: Validate our understanding and prepare for fixes

#### Task 0.1: Validate Diagnosis
```markdown
## Steps:
1. Create minimal test harness to verify each issue
2. Document actual vs expected behavior
3. Confirm root causes match diagnosis
4. Update BACKUP_PLANS.md if diagnosis incorrect

## TDD Approach:
- Write failing tests that reproduce each issue
- Tests become regression prevention
- Use calibre-debug for live validation

## Context Gathering:
- Read: interface.py, config.py, __init__.py
- Grep: "actual_plugin", "config_widget", "embedding_model"
- Test: Create simple plugin to test Calibre patterns
```

#### Task 0.2: Database Migration Preparation
```markdown
## Steps:
1. Analyze current schema
2. Design new schema with all required fields
3. Create migration script with rollback
4. Test on copy of database

## Required Schema Changes:
- Add provider, model_name, dimensions to indexes table
- Add chunking_strategy, philosophy_mode fields
- Add index_version, book_hash for change detection
- Create index_versions table for history

## Safety:
- Backup database before migration
- Test rollback procedure
- Keep old columns during transition
```

#### Task 0.3: Dimension Mapping Research
```markdown
## Steps:
1. Create provider→model→dimension mapping
2. Verify with each provider's documentation
3. Handle models with configurable dimensions
4. Design auto-detection logic

## Mapping Structure:
providers = {
    'openai': {
        'text-embedding-3-small': 1536,
        'text-embedding-3-large': 3072,
        'ada-002': 1536
    },
    'vertex_ai': {
        'textembedding-gecko': 768,
        'textembedding-gecko-multilingual': 768
    },
    'cohere': {
        'embed-v3': 1024,
        'embed-multilingual-v3': 1024
    }
}
```

### Phase 1: Critical Integration Fixes (4-5 hours)

**Reference**: UI_BACKEND_INTEGRATION_DIAGNOSIS.md Issues #1-5

#### Task 1.1: Fix Plugin Reference Chain
```markdown
## TDD Process:
1. Write test: test_config_widget_can_access_interface()
2. Test fails: No plugin_interface attribute
3. Implement fix in __init__.py config_widget()
4. Test passes
5. Write test: test_connection_uses_correct_service()
6. Implement fix in config.py _test_connection()
7. Integration test with live Calibre

## Implementation Notes:
- Modify SemanticSearchPlugin.config_widget()
- Pass actual_plugin_ as plugin_interface
- Update ConfigWidget to use plugin_interface
- Add fallback for when interface not available

## Verification:
- Test Connection button works
- Correct provider used for testing
- Error messages are helpful
```

#### Task 1.2: Remove Configuration Conflicts
```markdown
## TDD Process:
1. Write test: test_single_model_configuration()
2. Test fails: Two widgets save to same key
3. Remove model_combo from indexing tab
4. Remove dimension selector (auto-detect instead)
5. Test passes
6. Write test: test_dimension_auto_detection()
7. Implement dimension mapping

## UI Changes:
- Delete lines creating model_combo (config.py:329-332)
- Delete save logic for model_combo (config.py:584)
- Add dimension display label to AI Provider tab
- Update on provider/model change

## Data Flow:
Provider Tab → Model Selection → Auto-detect Dimensions → Display Only
```

#### Task 1.3: Fix Index Manager Issues
```markdown
## TDD Process:
1. Write test: test_table_cells_read_only()
2. Make all cells non-editable
3. Write test: test_single_statistics_display()
4. Remove duplicate statistics
5. Write test: test_metadata_display()
6. Fix legacy/unknown display issue

## Specific Fixes:
- Set Qt.ItemIsEditable flag OFF for all cells
- Remove grid layout statistics (keep HTML only)
- Query actual metadata from database
- Handle legacy data gracefully
```

#### Task 1.4: Implement Service Registry
```markdown
## TDD Process:
1. Write test: test_service_recreation_on_config_change()
2. Implement ServiceRegistry class
3. Write test: test_service_caching()
4. Add configuration hash checking
5. Integration test: config changes reflect immediately

## Architecture:
ServiceRegistry
  ├── get_embedding_service() - Lazy creation
  ├── get_search_engine() - Lazy creation
  ├── clear_services() - Called on config change
  └── _config_hash() - Detect changes

## Integration:
- Replace direct service creation
- Call clear_services() in save_settings()
- Use registry throughout codebase
```

### Phase 2: Core Requirements Implementation (8-10 hours)

**Reference**: calibre-semantic-spec-02.md P0/P1 requirements

#### Task 2.1: Implement Chunking Strategies
```markdown
## Requirements:
- FR-013: Four chunking strategies
- PRR-001: Philosophy-aware processing

## TDD Implementation Order:
1. Base ChunkingStrategy interface
2. FixedSizeChunking (exists, refactor)
3. ParagraphBasedChunking
4. SemanticChunking (with philosophy mode)
5. SlidingWindowChunking
6. HybridChunking (recommended default)

## Test Cases Per Strategy:
- Basic text chunking
- Edge cases (empty, single char, huge)
- Overlap handling
- Philosophy text handling
- Performance benchmarks

## Integration:
- Update TextProcessor to use strategies
- Add strategy selection to config
- Store strategy used in index metadata
```

#### Task 2.2: Multi-Provider Fallback System
```markdown
## Requirements:
- FR-011: Automatic fallback on failure

## TDD Process:
1. Test: test_provider_fallback_on_failure()
2. Implement provider chain configuration
3. Test: test_fallback_order_respected()
4. Implement retry with next provider
5. Test: test_all_providers_fail_gracefully()
6. Implement mock provider as final fallback

## Configuration:
{
    "primary_provider": "openai",
    "fallback_providers": ["vertex_ai", "cohere"],
    "retry_count": 3,
    "fallback_to_mock": true
}

## Error Handling:
- Log each failure with reason
- Notify user of fallback
- Store which provider actually used
```

#### Task 2.3: Complete Index Metadata
```markdown
## Requirements:
- FR-010: Comprehensive index information
- FR-014: Change detection

## Implementation:
1. Extend database schema (via migration)
2. Update IndexingService to collect all metadata
3. Implement book hash calculation
4. Add language detection
5. Store all metadata during indexing

## Metadata Fields:
- book_id, provider, model_name
- dimensions, chunk_size, chunking_strategy
- philosophy_mode, language
- book_hash, created_at, index_version

## Change Detection:
- Calculate hash of book content + metadata
- Compare with stored hash
- Flag books needing reindexing
```

#### Task 2.4: Search Modes Implementation
```markdown
## Requirements:
- FR-004: Three search modes

## Modes:
1. Semantic (existing, optimize)
2. Keyword (new, integrate with FTS)
3. Hybrid (combine both approaches)

## TDD Process:
1. Test each mode independently
2. Test mode switching
3. Test result ranking/merging
4. Performance benchmarks

## UI Integration:
- Add mode selector to search dialog
- Remember user preference
- Show mode in results
```

### Phase 3: Architecture & Performance (4-5 hours)

#### Task 3.1: Performance Optimization
```markdown
## Requirements:
- NFR-001: <100ms search latency
- NFR-002: ≥50 books/hour indexing

## Optimizations:
1. Connection pooling for API calls
2. Batch embedding requests
3. Efficient vector operations
4. Query optimization
5. Caching improvements

## Benchmarking:
- Create performance test suite
- Measure before/after
- Profile bottlenecks
- Document results
```

#### Task 3.2: Error Handling & Resilience
```markdown
## Requirements:
- NFR-004: Graceful degradation

## Implementation:
1. Comprehensive error boundaries
2. Retry mechanisms
3. User-friendly error messages
4. Automatic recovery
5. Error reporting

## Test Scenarios:
- Network failures
- API quota exceeded
- Corrupt data
- Database locked
- Memory constraints
```

### Phase 4: Polish & Documentation (2-3 hours)

#### Task 4.1: UI Polish
```markdown
## Tasks:
1. Apply consistent theming
2. Add loading indicators
3. Improve error messages
4. Add tooltips/help text
5. Keyboard navigation

## Accessibility:
- Screen reader support
- High contrast mode
- Keyboard shortcuts
- Focus management
```

#### Task 4.2: Documentation
```markdown
## Updates:
1. User manual with screenshots
2. API documentation
3. Configuration guide
4. Troubleshooting guide
5. Developer documentation
```

## 🧪 Testing Strategy

### Test Categories
1. **Unit Tests** - Individual components
2. **Integration Tests** - Component interactions
3. **UI Tests** - User interface behavior
4. **Performance Tests** - Speed benchmarks
5. **Compatibility Tests** - Calibre versions

### TDD Cycle for Each Task
```python
# 1. RED - Write failing test
def test_new_feature():
    result = feature_under_test()
    assert result == expected_value  # Fails

# 2. GREEN - Make it pass (simplest way)
def feature_under_test():
    return expected_value  # Passes

# 3. REFACTOR - Improve implementation
def feature_under_test():
    # Proper implementation
    return calculated_value
```

### Coverage Requirements
- Minimum 80% overall
- 90% for critical paths
- 100% for data operations

## 🚨 Risk Mitigation

### Technical Risks
1. **Calibre API changes** → Test with multiple versions
2. **Database corruption** → Comprehensive backups
3. **Performance regression** → Continuous benchmarking
4. **Breaking changes** → Feature flags

### Process Risks
1. **Scope creep** → Strict phase boundaries
2. **Integration issues** → Incremental testing
3. **Burnout** → Realistic timelines

### Backup Plans
See BACKUP_PLANS.md for:
- Alternative approaches if diagnosis wrong
- Rollback procedures
- Emergency fixes
- Contingency timelines

## 📊 Progress Tracking

### Daily Checklist
- [ ] Review phase objectives
- [ ] Gather context (Read/Grep/Test)
- [ ] SPARC analysis for complex decisions
- [ ] TDD implementation
- [ ] Update tests
- [ ] Commit with meaningful message
- [ ] Update CHANGELOG.md
- [ ] Review tomorrow's tasks

### Phase Completion Criteria
- All tests passing
- Code review complete
- Documentation updated
- Performance validated
- No regressions
- PR approved and merged

## 🎯 Definition of Done

A task is DONE when:
1. All tests pass (including new ones)
2. Code coverage maintained/improved
3. Documentation updated
4. Performance benchmarks pass
5. No lint/type errors
6. Works in live Calibre
7. PR merged to main branch

## 📅 Timeline

### Week 1 (15-20 hours)
- Day 1: Phase 0 - Foundation (2-3h)
- Day 2-3: Phase 1 - Integration Fixes (4-5h)
- Day 4-7: Phase 2 - Core Requirements (8-10h)

### Week 2 (5-10 hours)
- Day 1-2: Phase 3 - Architecture (4-5h)
- Day 3: Phase 4 - Polish (2-3h)
- Day 4-5: Buffer/Testing/Release

## 🚀 Next Steps

1. Review this plan with stakeholders
2. Create BACKUP_PLANS.md
3. Set up development environment
4. Begin Phase 0 validation
5. Create first failing test

---

**Remember**: This plan is a guide, not a contract. Adapt based on discoveries during implementation. When in doubt, refer to SPARC analysis and TDD principles.