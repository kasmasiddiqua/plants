# Team Git Branching Strategy

## Team Members

- Developer 1: Plant Search Feature
- Developer 2: Plant Details Feature
- Developer 3: Plant Health Dashboard

## Branch Structure

- main: Stable and tested code.
- feature/plant-search: Search functionality.
- feature/plant-details: Plant information.
- feature/plant-health: Health dashboard.

## Workflow

1. Developers pull the latest main branch.
2. Create a separate feature branch.
3. Implement and test their features.
4. Commit changes using meaningful messages.
5. Push feature branches to GitHub.
6. Create Pull Requests for code review.
7. Merge approved features into main.

## Commit Message Convention

- feat: Add new functionality.
- fix: Fix bugs.
- docs: Update documentation.
- test: Add tests.
- merge: Merge feature branches.

## Conflict Resolution

When merge conflicts occur, developers
review the conflicting changes, resolve
them manually, test the code and commit
the resolved changes.
