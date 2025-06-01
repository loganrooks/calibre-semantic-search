# Documentation Index

**Last Updated**: 2025-06-01

## 📚 Documentation Organization

### **Essential Documents (Root Directory)**
- `PROJECT_STATUS.md` - Current project status and completion tracking
- `CLAUDE.md` - AI context, development rules, and comprehensive guide
- `CHANGELOG.md` - Version history and release notes
- `README.md` - Public project overview and getting started

### **Reference Documentation**

#### 📊 Analysis & Research
- `analysis/` - *Empty (moved to archive)*

#### 🔧 Development Resources
- `development/` - *Empty (development plans archived)*

#### 🎓 Lessons Learned
- `lessons/PLUGIN_INTEGRATION_LESSONS.md` - Calibre integration solutions
- `lessons/DEVELOPMENT_FEEDBACK.md` - Process violations and recovery

#### 📋 Planning & Future Work
- `planning/CONFIG_IMPROVEMENTS.md` - LiteLLM and configuration enhancements

#### 📖 User Documentation
- `terminology/UI_TERMINOLOGY.md` - User-facing language guidelines

#### 📄 General Reference
- `SUMMARY.md` - High-level implementation overview

### **Archived Documentation**

#### 📈 Historical Analysis (archive/analysis-snapshots/)
- `ANALYSIS_REPORT_CORE_COMPONENTS.md` (2025-05-29)
- `ANALYSIS_REPORT_FINAL_DIVERGENCES.md` (2025-05-29)
- `ANALYSIS_REPORT_FUNCTIONAL_REQUIREMENTS.md` (2025-05-29)

#### ❌ Failed Attempts (archive/failed-attempts/)
- `TDD_INTEGRATION_PLAN.md` - Failed TDD approach
- `UI_BACKEND_INTEGRATION_PSEUDOCODE.md` - Abandoned pseudocode
- `UI_BACKEND_INTEGRATION_VERIFICATION.md` - Abandoned verification
- `SALVAGE_ANALYSIS.md` - Recovery from TDD failure

#### 🗃️ Development Artifacts (archive/development-artifacts/)
- `DEVELOPMENT_ARTIFACTS_CLEANUP.md` - Previous cleanup documentation
- `IMPLEMENTATION_ANALYSIS.md` - Gap analysis (superseded by PROJECT_STATUS.md)

## 📊 Documentation Health Status

**Current Status**: ✅ **HEALTHY**
- Root files: 4/4 ✅ (Perfect)
- Stale documents: 0 ✅
- Archive ratio: 73% ✅ (11/15 docs properly archived)
- Maintenance burden: Low ✅

## 🔄 Maintenance Schedule

### After Each Session
- [ ] Update PROJECT_STATUS.md
- [ ] Update CLAUDE.md if needed
- [ ] Move completed planning docs to archive

### Weekly (Friday)
- [ ] Check for stale documents (>60 days)
- [ ] Review archive candidates
- [ ] Update this INDEX.md

### Monthly
- [ ] Consolidate overlapping content
- [ ] Verify all links work
- [ ] Archive outdated analysis

## 📖 How to Use This Documentation

### Starting Work
```bash
# Check current status
cat PROJECT_STATUS.md | head -20

# Check for relevant lessons
grep -r "keyword" docs/lessons/

# Review planning docs
ls docs/planning/
```

### Finding Information
1. **Current Status**: PROJECT_STATUS.md
2. **How-To & Troubleshooting**: docs/lessons/
3. **Future Plans**: docs/planning/
4. **Historical Context**: archive/ directories

### Creating New Documents
1. Check if topic already exists
2. Choose appropriate directory (docs/ vs archive/)
3. Use descriptive names
4. Update this INDEX.md

## 🚨 Red Flags

Watch for these warning signs:
- More than 4 files in root directory
- Documents not updated in 60+ days
- Multiple docs covering same topic
- Planning docs for completed work still active

If you see these, follow the cleanup process in CLAUDE.md.