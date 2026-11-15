# Test9 Local Data Controls Design

## Intent

Ship an independent test9 Windows build and let users safely clear local wrong-question state, practice history, or only the learning-dashboard baseline from Settings.

## Safety and semantics

- Clear wrong notebook: delete only `wrong_questions` rows.
- Clear practice history: delete `sessions`; foreign-key cascade deletes `session_items`, while wrong questions remain.
- Reset learning overview: preserve history and wrong questions, store the current highest answer-item id, and calculate dashboard practice totals, trends, type progress, and recent activity only from newer answers.
- Every Settings action creates a database backup before changing data, uses an explicit confirmation message, and refreshes all affected pages immediately.
- Questions, banks, explanation packages, attachments, templates, and backups are never deleted by these controls.

## Architecture

Upgrade SQLite to schema v4 with a small `app_settings(key, value)` table. Add transactional database APIs for the three operations. The overview reset uses a monotonic `session_items.id` high-water mark, avoiding clock-resolution and timezone errors, and applies it consistently to every query in `learning_overview`.

Settings exposes a separate “本地学习数据” card with three destructive-looking but clearly scoped actions. `SettingsPage` emits a data-changed signal after success; `MainWindow` connects it to its existing `refresh_all` path.

## Packaging

Update the visible version and installer version to `1.6.0-test9`. Build with PyInstaller and Inno Setup. The installer and portable folder are copied to `D:\工具\刷题软件\test9`; test8 remains unchanged.

## Alternatives considered

- Deleting session data to reset the overview was rejected because it would silently destroy history.
- Resetting all learning data with one button was rejected because the user asked for separate controls.
- Keeping schema v3 and storing the reset time in a sidecar file was rejected because backups/restores would no longer capture all application state.

## Verification

Tests cover migration/idempotency, deletion scope, overview cutoff, backup-before-delete UI behavior, confirmation cancellation, page refresh signaling, and unchanged question/package counts. Final verification includes the full pytest suite, EXE smoke launch, installer generation, hashes, and target-directory audit.
