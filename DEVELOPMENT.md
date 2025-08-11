# Malfian's Vault - Development Guidelines

## Branching Strategy

### Stable Release Branch: `master`
- Contains only tested, stable code
- Tagged with release versions (v2.0.2, v2.0.3, etc.)
- **DO NOT** push directly to master for new features
- Only merge from `dev` branch after thorough testing

### Development Branch: `dev` 
- All new feature development happens here
- Experimental changes and bug fixes go here first
- Test thoroughly before merging to master

## Development Workflow

### For New Features/Bug Fixes:
1. **Switch to dev branch**: `git checkout dev`
2. **Pull latest changes**: `git pull origin dev`
3. **Create feature branch** (optional): `git checkout -b feature/new-feature`
4. **Make your changes and test thoroughly**
5. **Commit changes**: `git commit -m "Description"`
6. **Push to dev**: `git push origin dev` (or feature branch)
7. **Test extensively** - especially house scanning scenarios!

### For Stable Releases:
1. **Test dev branch thoroughly** with real-world scenarios
2. **Switch to master**: `git checkout master`
3. **Merge dev**: `git merge dev`
4. **Create release tag**: `git tag -a v2.0.3 -m "Release notes"`
5. **Push master and tag**: `git push origin master && git push origin v2.0.3`

## Critical Testing Areas

Before any master merge, test these scenarios:
- [ ] Regular character scanning (multiple characters)
- [ ] House scanning with multi-room setups
- [ ] Web interface displays characters correctly (not ANSI codes)
- [ ] CSV files have reasonable line counts (~65 for 2 chars, not thousands)
- [ ] No ANSI codes leaking to terminal during scans
- [ ] Fresh installation works without corruption

## Branch Status

- **master**: v2.0.2 - Stable, production-ready
- **dev**: Development branch for all new changes

## Notes

v2.0.2 fixes the critical CSV corruption issue where house inventory `raw_line` fields with ANSI codes were breaking CSV structure and causing the character table to display ANSI codes as character names.

All future development should use this branching strategy to preserve the stability of the master branch.