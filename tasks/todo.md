# Multi-game Launcher Tasks

## Phase 1: Foundations

- [x] Task 1: Lock down the NTE reference contract.
- [x] Task 2: Add persisted game context.
- [x] Task 3: Implement NTE path, status, launch, and stop.

### Checkpoint: Foundations

- [x] New focused tests pass.
- [x] Existing tests pass.
- [x] Wuwa remains the backward-compatible default.

## Phase 2: NTE Features

- [x] Task 4: Add transactional NTE translation management.
- [x] Task 5: Add pinned AlteriaX NTE performance presets.

### Checkpoint: NTE Backend

- [x] Translation failure preserves the working installation.
- [x] NTE preset restore is exact.
- [x] No NTE operation touches Wuwa paths.

## Phase 3: User Interface

- [x] Task 6: Add game selection and NTE theme shell.
- [x] Task 7: Connect shared NTE actions and progress UI.
- [x] Task 8: Connect NTE performance and feature visibility.

### Checkpoint: Complete UI

- [x] NTE end-to-end flow works.
- [x] Wuwa themes and features remain intact.
- [x] NTE contains no custom cursor.

## Phase 4: Verification and Packaging

- [x] Task 9: Regression-test and package locally.

### Checkpoint: Complete

- [x] Full test and syntax suite passes.
- [x] Extracted AppImage contains both game implementations.
- [x] No release or GitHub mutation was performed.
