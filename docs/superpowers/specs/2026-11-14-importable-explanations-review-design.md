# Importable Explanations and Readable Review Design

## Intent

Add separately importable mechanic explanation packages, improve sequential-practice feedback, and replace the exam history table with a readable per-question review. Explanation documents and extracted records remain user data and are never bundled with the application.

## Goals

- Import the three supplied DOCX structures as 599 junior, 792 intermediate, and 642 advanced fill-blank, choice, and true-false entries.
- Match only by subject, level, question type, normalized stem fingerprint, and normalized reference answer.
- Keep package data separate from `questions.explanation`, with dynamic newest-successful-package precedence and automatic fallback after deletion.
- Let sequential practice auto-advance about 350 ms after a correct non-final answer while retaining completed-answer review and locking.
- Use one per-question review component for both just-submitted exams and historical sessions.

## Non-goals

- No fuzzy matching, AI matching, or manual forced attachment.
- No changes to scoring rules or exam navigation before submission.
- No bundled DOCX files, extracted explanation fixtures, user databases, caches, build outputs, or generated egg-info changes.

## Constraints

- Existing databases must migrate repeatably without losing questions, wrong-question state, scores, or history.
- Each selected DOCX is validated and imported in its own transaction.
- A duplicate is based on SHA-256 of normalized package content, independent of filename.
- Package explanations are read dynamically; original question explanations stay intact.
- The UI must fit 1366x768 without horizontal review-table overflow.

## Approaches

### Chosen approach: dynamic exact overlay

Store packages and entries in schema v3. Normalize both imported explanation entries and live questions through the same functions. Resolve an explanation at question-read or history-read time, choosing the newest exact-answer match. Status counts are computed from current questions, so importing either side first works without reconciliation jobs.

This approach directly satisfies deletion fallback and historical dynamic refresh without mutating question rows or snapshots.

### Rejected approach: copy explanation into questions

Copying package text into `questions.explanation` would erase provenance, make deletion fallback unreliable, and prevent historical records from following current packages.

### Rejected approach: persistent match rows

A separate materialized match table could speed lookups, but every question/package import, edit, and delete would require reconciliation. The current local dataset size does not justify that complexity; indexed exact lookups are sufficient.

## Data and matching design

`explanation_packages` stores name, filename, subject, level, normalized content hash, and import time. `explanation_entries` stores package id, source question type and number, normalized stem fingerprint, normalized answer, original stem, and explanation.

Question-bank subject and level are deliberately conservative: only names/source filenames containing `机修钳工` and exactly one of `初级`, `中级`, or `高级` are eligible. Unknown levels and other subjects never match.

The stem normalizer removes source numbering, embedded answer marks, choice option blocks, terminal judgment marks, whitespace, and harmless punctuation differences while preserving semantic characters. Fill blanks become one canonical blank token. Answers normalize by type: ordered blank groups, sorted choice letters, or boolean values. Choice type is single or multiple according to the reference-answer letter count.

An entry is:

- matched when an eligible question has the same subject, level, type, fingerprint, and answer;
- conflict when the first four fields match but no candidate answer matches;
- pending when no eligible question shares the first four fields.

## UI design

The bank page gains an `解析资料` button opening a dedicated manager. It imports multiple DOCX files independently, shows package metadata and four counts, prompts to replace duplicate content, and warns that deletion removes only explanations.

Sequential practice keeps the existing `AnswerReviewPanel` and `QuestionNavigator`. Correct non-final answers schedule a guarded 350 ms move; wrong/partial answers remain; the final correct answer stays visible with a completion message.

`ExamReviewDialog` replaces the seven-column table. A scrollable left detail card shows stem, options, result, user answer, reference answer, score, explanation/solution, and attachments. The right side reuses `QuestionNavigator`; previous, next, and close controls stay reachable. The component is only constructed after exam submission and is reused by history.

## Validation

Tests cover real-document counts, parser completeness, migration/idempotency, import order, strict subject/level/type/stem/answer matching, conflicts, duplicate replacement atomicity, delete preservation/fallback, multiple-package precedence, sequential timing/locking/review, exam secrecy and review navigation, attachments, and 1366x768 layout. The final gate is the complete pytest suite plus a clean diff audit.
