from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from .domain import DuplicatePolicy, ImportSummary, Question, QuestionAsset, QuestionType
from .explanation_packages import (
    DuplicateExplanationPackage,
    ExplanationPackage,
    classify_mechanic_source,
    normalize_answer,
    normalize_stem,
)


SCHEMA_VERSION = 4


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        connection = self.connect()
        try:
            has_version_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ).fetchone()
            if not has_version_table:
                self._create_v4_schema(connection)
                connection.commit()
                return
            row = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if row is None:
                raise RuntimeError("数据库版本信息缺失")
            version = int(row["version"])
            if version > SCHEMA_VERSION:
                raise RuntimeError("数据库版本高于当前程序，无法打开")
            if version < SCHEMA_VERSION:
                connection.execute("BEGIN")
                try:
                    if version == 1:
                        self._migrate_v1_to_v2(connection)
                        version = 2
                    if version == 2:
                        self._migrate_v2_to_v3(connection)
                        version = 3
                    if version == 3:
                        self._migrate_v3_to_v4(connection)
                        version = 4
                    connection.execute("UPDATE schema_version SET version=?", (version,))
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
            if version != SCHEMA_VERSION:
                raise RuntimeError(f"不支持的数据库版本：{version}")
        finally:
            connection.close()

    def _create_v4_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
                CREATE TABLE schema_version (version INTEGER NOT NULL);
                INSERT INTO schema_version(version) VALUES (4);

                CREATE TABLE banks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    source_filename TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_id INTEGER NOT NULL REFERENCES banks(id) ON DELETE CASCADE,
                    fingerprint TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    stem TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    answer_json TEXT NOT NULL,
                    aliases_json TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    solution TEXT NOT NULL DEFAULT '',
                    requires_manual_review INTEGER NOT NULL DEFAULT 0,
                    category TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    source_order INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(bank_id, fingerprint)
                );

                CREATE TABLE question_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                    mime_type TEXT NOT NULL,
                    data BLOB NOT NULL,
                    position INTEGER NOT NULL,
                    alt_text TEXT NOT NULL DEFAULT ''
                );

                CREATE INDEX idx_question_assets_order
                    ON question_assets(question_id, position, id);

                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT NOT NULL,
                    filters_json TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    score INTEGER,
                    total INTEGER
                );

                CREATE TABLE session_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    question_id INTEGER,
                    snapshot_json TEXT NOT NULL,
                    user_answer_json TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    earned_points INTEGER NOT NULL,
                    answered_at TEXT NOT NULL
                );

                CREATE TABLE wrong_questions (
                    question_id INTEGER PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
                    wrong_count INTEGER NOT NULL DEFAULT 1,
                    last_wrong_at TEXT NOT NULL,
                    mastered INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE explanation_packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    level TEXT NOT NULL,
                    content_hash TEXT NOT NULL UNIQUE,
                    imported_at TEXT NOT NULL
                );

                CREATE TABLE explanation_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL REFERENCES explanation_packages(id) ON DELETE CASCADE,
                    question_type TEXT NOT NULL,
                    source_number INTEGER NOT NULL,
                    original_stem TEXT NOT NULL,
                    stem_fingerprint TEXT NOT NULL,
                    normalized_answer TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    UNIQUE(package_id, question_type, source_number)
                );

                CREATE INDEX idx_explanation_entries_match
                    ON explanation_entries(question_type, stem_fingerprint, normalized_answer);
                CREATE INDEX idx_explanation_entries_package
                    ON explanation_entries(package_id, source_number);

                CREATE TABLE app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """
        )

    def _migrate_v1_to_v2(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            "ALTER TABLE questions ADD COLUMN solution TEXT NOT NULL DEFAULT ''"
        )
        connection.execute(
            "ALTER TABLE questions ADD COLUMN requires_manual_review INTEGER NOT NULL DEFAULT 0"
        )
        connection.execute(
            """CREATE TABLE question_assets (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                   mime_type TEXT NOT NULL,
                   data BLOB NOT NULL,
                   position INTEGER NOT NULL,
                   alt_text TEXT NOT NULL DEFAULT ''
               )"""
        )
        connection.execute(
            "CREATE INDEX idx_question_assets_order ON question_assets(question_id, position, id)"
        )

    def _migrate_v2_to_v3(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE explanation_packages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   filename TEXT NOT NULL,
                   subject TEXT NOT NULL,
                   level TEXT NOT NULL,
                   content_hash TEXT NOT NULL UNIQUE,
                   imported_at TEXT NOT NULL
               )"""
        )
        connection.execute(
            """CREATE TABLE explanation_entries (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   package_id INTEGER NOT NULL REFERENCES explanation_packages(id) ON DELETE CASCADE,
                   question_type TEXT NOT NULL,
                   source_number INTEGER NOT NULL,
                   original_stem TEXT NOT NULL,
                   stem_fingerprint TEXT NOT NULL,
                   normalized_answer TEXT NOT NULL,
                   explanation TEXT NOT NULL,
                   UNIQUE(package_id, question_type, source_number)
               )"""
        )
        connection.execute(
            """CREATE INDEX idx_explanation_entries_match
               ON explanation_entries(question_type, stem_fingerprint, normalized_answer)"""
        )
        connection.execute(
            """CREATE INDEX idx_explanation_entries_package
               ON explanation_entries(package_id, source_number)"""
        )

    def _migrate_v3_to_v4(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE app_settings (
                   key TEXT PRIMARY KEY,
                   value TEXT NOT NULL
               )"""
        )

    def ensure_bank(self, name: str, source_filename: str = "") -> int:
        with self.connection() as connection:
            return self._ensure_bank_with_connection(connection, name, source_filename)

    def _ensure_bank_with_connection(
        self, connection: sqlite3.Connection, name: str, source_filename: str = ""
    ) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        connection.execute(
            """INSERT INTO banks(name, source_filename, created_at, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 source_filename=CASE WHEN excluded.source_filename='' THEN banks.source_filename ELSE excluded.source_filename END,
                 updated_at=excluded.updated_at""",
            (name, source_filename, now, now),
        )
        row = connection.execute("SELECT id FROM banks WHERE name=?", (name,)).fetchone()
        return int(row["id"])

    def get_banks(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """SELECT b.*, COUNT(q.id) AS question_count
                   FROM banks b LEFT JOIN questions q ON q.bank_id=b.id
                   GROUP BY b.id ORDER BY b.name"""
            ).fetchall()
        return [dict(row) for row in rows]

    def import_explanation_package(
        self,
        package: ExplanationPackage,
        *,
        replace_package_id: int | None = None,
    ) -> int:
        with self.transaction() as connection:
            duplicate = connection.execute(
                "SELECT id, filename FROM explanation_packages WHERE content_hash=?",
                (package.content_hash,),
            ).fetchone()
            if duplicate is not None and replace_package_id is None:
                raise DuplicateExplanationPackage(
                    int(duplicate["id"]), str(duplicate["filename"])
                )
            if duplicate is not None and int(duplicate["id"]) != replace_package_id:
                raise DuplicateExplanationPackage(
                    int(duplicate["id"]), str(duplicate["filename"])
                )
            if replace_package_id is not None:
                existing = connection.execute(
                    "SELECT id FROM explanation_packages WHERE id=?",
                    (replace_package_id,),
                ).fetchone()
                if existing is None:
                    raise ValueError("要替换的解析资料不存在")
                connection.execute(
                    "DELETE FROM explanation_packages WHERE id=?",
                    (replace_package_id,),
                )
            cursor = connection.execute(
                """INSERT INTO explanation_packages(
                       name, filename, subject, level, content_hash, imported_at
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    package.name,
                    package.filename,
                    package.subject,
                    package.level,
                    package.content_hash,
                    datetime.now().isoformat(timespec="microseconds"),
                ),
            )
            package_id = int(cursor.lastrowid)
            connection.executemany(
                """INSERT INTO explanation_entries(
                       package_id, question_type, source_number, original_stem,
                       stem_fingerprint, normalized_answer, explanation
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        package_id,
                        entry.question_type.value,
                        entry.source_number,
                        entry.original_stem,
                        entry.stem_fingerprint,
                        entry.normalized_answer,
                        entry.explanation,
                    )
                    for entry in package.entries
                ],
            )
            return package_id

    def delete_explanation_package(self, package_id: int) -> None:
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM explanation_packages WHERE id=?", (package_id,)
            )

    def find_explanation_package_by_hash(
        self, content_hash: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM explanation_packages WHERE content_hash=?",
                (content_hash,),
            ).fetchone()
        return dict(row) if row else None

    def _question_match_key(
        self, question: Question, source_filename: str = ""
    ) -> tuple[str, str, str, str, str] | None:
        classification = classify_mechanic_source(
            question.bank_name, source_filename
        )
        if classification is None:
            return None
        subject, level = classification
        try:
            answer = normalize_answer(question.question_type, question.answer)
        except ValueError:
            return None
        return (
            subject,
            level,
            question.question_type.value,
            normalize_stem(question.question_type, question.stem),
            answer,
        )

    def _resolve_explanation_with_connection(
        self,
        connection: sqlite3.Connection,
        question: Question,
        source_filename: str = "",
    ) -> str | None:
        key = self._question_match_key(question, source_filename)
        if key is None:
            return None
        row = connection.execute(
            """SELECT entry.explanation
               FROM explanation_entries entry
               JOIN explanation_packages package ON package.id=entry.package_id
               WHERE package.subject=? AND package.level=?
                 AND entry.question_type=? AND entry.stem_fingerprint=?
                 AND entry.normalized_answer=?
               ORDER BY package.imported_at DESC, package.id DESC, entry.id DESC
               LIMIT 1""",
            key,
        ).fetchone()
        return str(row["explanation"]) if row else None

    def list_explanation_packages(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            packages = connection.execute(
                "SELECT * FROM explanation_packages ORDER BY imported_at DESC, id DESC"
            ).fetchall()
            entries = connection.execute(
                "SELECT * FROM explanation_entries ORDER BY package_id, id"
            ).fetchall()
            question_rows = connection.execute(
                """SELECT q.*, b.name AS bank_name, b.source_filename AS bank_source_filename
                   FROM questions q JOIN banks b ON b.id=q.bank_id"""
            ).fetchall()
        available: dict[tuple[str, str, str, str], set[str]] = {}
        for row in question_rows:
            question = self._row_to_question(row)
            key = self._question_match_key(
                question, str(row["bank_source_filename"])
            )
            if key is not None:
                available.setdefault(key[:4], set()).add(key[4])
        entries_by_package: dict[int, list[sqlite3.Row]] = {}
        for entry in entries:
            entries_by_package.setdefault(int(entry["package_id"]), []).append(entry)
        results: list[dict[str, Any]] = []
        for package in packages:
            item = dict(package)
            matched = pending = conflicts = 0
            package_entries = entries_by_package.get(int(package["id"]), [])
            for entry in package_entries:
                base = (
                    str(package["subject"]),
                    str(package["level"]),
                    str(entry["question_type"]),
                    str(entry["stem_fingerprint"]),
                )
                answers = available.get(base)
                if not answers:
                    pending += 1
                elif str(entry["normalized_answer"]) in answers:
                    matched += 1
                else:
                    conflicts += 1
            item.update(
                total_count=len(package_entries),
                matched_count=matched,
                pending_count=pending,
                conflict_count=conflicts,
            )
            results.append(item)
        return results

    def upsert_question(self, bank_id: int, question: Question, overwrite: bool = False) -> int:
        with self.connection() as connection:
            return self._upsert_question_with_connection(connection, bank_id, question, overwrite)

    def _upsert_question_with_connection(
        self,
        connection: sqlite3.Connection,
        bank_id: int,
        question: Question,
        overwrite: bool,
    ) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        values = (
            question.question_type.value,
            question.stem,
            json.dumps(question.options, ensure_ascii=False),
            json.dumps(question.answer, ensure_ascii=False),
            json.dumps(question.aliases, ensure_ascii=False),
            question.explanation,
            question.solution,
            int(question.requires_manual_review),
            question.category,
            question.difficulty,
            json.dumps(question.tags, ensure_ascii=False),
            int(question.points or 1),
            int(question.source_order),
        )
        existing = connection.execute(
            "SELECT id FROM questions WHERE bank_id=? AND fingerprint=?",
            (bank_id, question.fingerprint),
        ).fetchone()
        if existing:
            question_id = int(existing["id"])
            if overwrite:
                connection.execute(
                    """UPDATE questions SET question_type=?, stem=?, options_json=?, answer_json=?,
                       aliases_json=?, explanation=?, solution=?, requires_manual_review=?,
                       category=?, difficulty=?, tags_json=?, points=?, source_order=?,
                       updated_at=? WHERE id=?""",
                    (*values, now, question_id),
                )
                self._replace_assets(connection, question_id, question.assets)
            return question_id
        cursor = connection.execute(
            """INSERT INTO questions(
                   bank_id, fingerprint, question_type, stem, options_json, answer_json,
                   aliases_json, explanation, solution, requires_manual_review, category,
                   difficulty, tags_json, points, source_order, created_at, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (bank_id, question.fingerprint, *values, now, now),
        )
        question_id = int(cursor.lastrowid)
        self._replace_assets(connection, question_id, question.assets)
        return question_id

    def _replace_assets(
        self,
        connection: sqlite3.Connection,
        question_id: int,
        assets: list[QuestionAsset],
    ) -> None:
        connection.execute("DELETE FROM question_assets WHERE question_id=?", (question_id,))
        connection.executemany(
            """INSERT INTO question_assets(question_id, mime_type, data, position, alt_text)
               VALUES (?, ?, ?, ?, ?)""",
            [
                (
                    question_id,
                    asset.mime_type,
                    sqlite3.Binary(asset.data),
                    int(asset.position),
                    asset.alt_text,
                )
                for asset in assets
            ],
        )

    def _load_assets(
        self, connection: sqlite3.Connection, question_id: int
    ) -> list[QuestionAsset]:
        rows = connection.execute(
            """SELECT mime_type, data, position, alt_text
               FROM question_assets WHERE question_id=? ORDER BY position, id""",
            (question_id,),
        ).fetchall()
        return [
            QuestionAsset(
                mime_type=str(row["mime_type"]),
                data=bytes(row["data"]),
                position=int(row["position"]),
                alt_text=str(row["alt_text"]),
            )
            for row in rows
        ]

    def commit_import(
        self,
        questions: list[Question],
        source_filename: str,
        duplicate_policy: DuplicatePolicy,
    ) -> ImportSummary:
        summary = ImportSummary()
        with self.transaction() as connection:
            for question in questions:
                bank_id = self._ensure_bank_with_connection(
                    connection, question.bank_name, source_filename
                )
                existing = connection.execute(
                    "SELECT id FROM questions WHERE bank_id=? AND fingerprint=?",
                    (bank_id, question.fingerprint),
                ).fetchone()
                if existing is not None and duplicate_policy is DuplicatePolicy.SKIP:
                    summary.skipped += 1
                    continue
                self._upsert_question_with_connection(
                    connection,
                    bank_id,
                    question,
                    duplicate_policy is DuplicatePolicy.OVERWRITE,
                )
                if existing is None:
                    summary.inserted += 1
                else:
                    summary.overwritten += 1
        return summary

    def _row_to_question(
        self, row: sqlite3.Row, assets: list[QuestionAsset] | None = None
    ) -> Question:
        return Question(
            id=int(row["id"]),
            bank_id=int(row["bank_id"]),
            bank_name=str(row["bank_name"]),
            question_type=QuestionType(row["question_type"]),
            stem=str(row["stem"]),
            options=json.loads(row["options_json"]),
            answer=json.loads(row["answer_json"]),
            aliases=json.loads(row["aliases_json"]),
            explanation=str(row["explanation"]),
            solution=str(row["solution"]),
            requires_manual_review=bool(row["requires_manual_review"]),
            assets=assets or [],
            category=str(row["category"]),
            difficulty=str(row["difficulty"]),
            tags=json.loads(row["tags_json"]),
            points=int(row["points"]),
            source_order=int(row["source_order"]),
        )

    def get_question(
        self, question_id: int, *, include_package_explanation: bool = True
    ) -> Question | None:
        with self.connection() as connection:
            row = connection.execute(
                """SELECT q.*, b.name AS bank_name,
                          b.source_filename AS bank_source_filename
                   FROM questions q JOIN banks b ON b.id=q.bank_id WHERE q.id=?""",
                (question_id,),
            ).fetchone()
            assets = self._load_assets(connection, question_id) if row else []
            if row is None:
                return None
            question = self._row_to_question(row, assets)
            if include_package_explanation:
                package_explanation = self._resolve_explanation_with_connection(
                    connection, question, str(row["bank_source_filename"])
                )
                if package_explanation is not None:
                    question.explanation = package_explanation
            return question

    def find_question_id(self, bank_id: int, fingerprint: str) -> int | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id FROM questions WHERE bank_id=? AND fingerprint=?",
                (bank_id, fingerprint),
            ).fetchone()
        return int(row["id"]) if row else None

    def list_questions(
        self,
        *,
        bank_ids: list[int] | None = None,
        category: str = "",
        question_types: list[QuestionType] | None = None,
        difficulty: str = "",
        tag: str = "",
        wrong_only: bool = False,
        ordered: bool = False,
    ) -> list[Question]:
        clauses: list[str] = []
        params: list[Any] = []
        if bank_ids:
            clauses.append(f"q.bank_id IN ({','.join('?' for _ in bank_ids)})")
            params.extend(bank_ids)
        if category:
            clauses.append("q.category=?")
            params.append(category)
        if question_types:
            clauses.append(f"q.question_type IN ({','.join('?' for _ in question_types)})")
            params.extend(item.value for item in question_types)
        if difficulty:
            clauses.append("q.difficulty=?")
            params.append(difficulty)
        if tag:
            clauses.append("q.tags_json LIKE ?")
            params.append(f'%"{tag}"%')
        join = "JOIN wrong_questions w ON w.question_id=q.id AND w.mastered=0" if wrong_only else ""
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order = "ORDER BY q.bank_id, q.source_order, q.id" if ordered else "ORDER BY q.id"
        query = f"SELECT q.*, b.name AS bank_name, b.source_filename AS bank_source_filename FROM questions q JOIN banks b ON b.id=q.bank_id {join} {where} {order}"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
            questions: list[Question] = []
            for row in rows:
                question = self._row_to_question(
                    row, self._load_assets(connection, int(row["id"]))
                )
                package_explanation = self._resolve_explanation_with_connection(
                    connection, question, str(row["bank_source_filename"])
                )
                if package_explanation is not None:
                    question.explanation = package_explanation
                questions.append(question)
        return questions

    def delete_question(self, question_id: int) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM questions WHERE id=?", (question_id,))

    def update_question(self, question_id: int, question: Question) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self.connection() as connection:
            connection.execute(
                """UPDATE questions SET fingerprint=?, question_type=?, stem=?, options_json=?,
                   answer_json=?, aliases_json=?, explanation=?, solution=?,
                   requires_manual_review=?, category=?, difficulty=?, tags_json=?, points=?,
                   source_order=?, updated_at=? WHERE id=?""",
                (
                    question.fingerprint,
                    question.question_type.value,
                    question.stem,
                    json.dumps(question.options, ensure_ascii=False),
                    json.dumps(question.answer, ensure_ascii=False),
                    json.dumps(question.aliases, ensure_ascii=False),
                    question.explanation,
                    question.solution,
                    int(question.requires_manual_review),
                    question.category,
                    question.difficulty,
                    json.dumps(question.tags, ensure_ascii=False),
                    question.points,
                    question.source_order,
                    now,
                    question_id,
                ),
            )
            self._replace_assets(connection, question_id, question.assets)

    def delete_bank(self, bank_id: int) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM banks WHERE id=?", (bank_id,))

    def create_session(self, mode: str, filters: dict[str, Any]) -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO sessions(mode, filters_json, started_at) VALUES (?, ?, ?)",
                (mode, json.dumps(filters, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")),
            )
            return int(cursor.lastrowid)

    def save_session_item(
        self,
        session_id: int,
        question: Question,
        user_answer: Any,
        is_correct: bool,
        earned_points: int,
    ) -> None:
        with self.connection() as connection:
            self._save_session_item_with_connection(
                connection, session_id, question, user_answer, is_correct, earned_points
            )

    def _save_session_item_with_connection(
        self,
        connection: sqlite3.Connection,
        session_id: int,
        question: Question,
        user_answer: Any,
        is_correct: bool,
        earned_points: int,
    ) -> None:
        snapshot = question.snapshot()
        if question.id is not None:
            source_row = connection.execute(
                "SELECT explanation FROM questions WHERE id=?", (question.id,)
            ).fetchone()
            if source_row is not None:
                snapshot["explanation"] = str(source_row["explanation"])
        connection.execute(
            """INSERT INTO session_items(
                   session_id, question_id, snapshot_json, user_answer_json,
                   is_correct, earned_points, answered_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                question.id,
                json.dumps(snapshot, ensure_ascii=False),
                json.dumps(user_answer, ensure_ascii=False),
                int(is_correct),
                earned_points,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        if not is_correct and question.id is not None:
            now = datetime.now().isoformat(timespec="seconds")
            connection.execute(
                """INSERT INTO wrong_questions(question_id, wrong_count, last_wrong_at, mastered)
                   VALUES (?, 1, ?, 0)
                   ON CONFLICT(question_id) DO UPDATE SET
                     wrong_count=wrong_count+1, last_wrong_at=excluded.last_wrong_at, mastered=0""",
                (question.id, now),
            )

    def save_completed_exam(
        self,
        session_id: int,
        rows: list[tuple[Question, Any, bool, int]],
        score: int,
        total: int,
    ) -> None:
        with self.transaction() as connection:
            for question, user_answer, is_correct, earned_points in rows:
                self._save_session_item_with_connection(
                    connection,
                    session_id,
                    question,
                    user_answer,
                    is_correct,
                    earned_points,
                )
            connection.execute(
                "UPDATE sessions SET completed_at=?, score=?, total=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), score, total, session_id),
            )

    def complete_session(self, session_id: int, score: int, total: int) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE sessions SET completed_at=?, score=?, total=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), score, total, session_id),
            )

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                return None
            items = connection.execute(
                "SELECT * FROM session_items WHERE session_id=? ORDER BY id", (session_id,)
            ).fetchall()
            result = dict(row)
            result["filters"] = json.loads(result.pop("filters_json"))
            result["items"] = []
            for item in items:
                snapshot = json.loads(item["snapshot_json"])
                source_filename = ""
                if item["question_id"] is not None:
                    source_row = connection.execute(
                        """SELECT b.source_filename
                           FROM questions q JOIN banks b ON b.id=q.bank_id
                           WHERE q.id=?""",
                        (item["question_id"],),
                    ).fetchone()
                    if source_row is not None:
                        source_filename = str(source_row["source_filename"])
                try:
                    historical_question = Question(
                        id=snapshot.get("id"),
                        bank_id=snapshot.get("bank_id"),
                        bank_name=str(snapshot.get("bank_name") or ""),
                        question_type=QuestionType(snapshot["question_type"]),
                        stem=str(snapshot.get("stem") or ""),
                        options=dict(snapshot.get("options") or {}),
                        answer=snapshot.get("answer"),
                        explanation=str(snapshot.get("explanation") or ""),
                        solution=str(snapshot.get("solution") or ""),
                        points=int(snapshot.get("points") or 0),
                    )
                except (KeyError, TypeError, ValueError):
                    historical_question = None
                if historical_question is not None:
                    package_explanation = self._resolve_explanation_with_connection(
                        connection, historical_question, source_filename
                    )
                    if package_explanation is not None:
                        snapshot["explanation"] = package_explanation
                result["items"].append(
                    {
                        **dict(item),
                        "snapshot": snapshot,
                        "user_answer": json.loads(item["user_answer_json"]),
                    }
                )
        return result

    def list_sessions(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def clear_wrong_questions(self) -> int:
        with self.transaction() as connection:
            count = int(
                connection.execute("SELECT COUNT(*) FROM wrong_questions").fetchone()[0]
            )
            connection.execute("DELETE FROM wrong_questions")
        return count

    def clear_practice_history(self) -> int:
        with self.transaction() as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])
            connection.execute("DELETE FROM sessions")
        return count

    def reset_learning_overview(self) -> int:
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(id), 0) FROM session_items"
            ).fetchone()
            cutoff = int(row[0])
            connection.execute(
                """INSERT INTO app_settings(key, value)
                   VALUES ('learning_overview_after_item_id', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (str(cutoff),),
            )
        return cutoff

    @staticmethod
    def _learning_overview_cutoff(connection: sqlite3.Connection) -> int:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key='learning_overview_after_item_id'"
        ).fetchone()
        if row is None:
            return 0
        try:
            return max(0, int(row["value"]))
        except (TypeError, ValueError):
            return 0

    def learning_overview(self, days: int = 7) -> dict[str, Any]:
        days = max(1, int(days))
        today = date.today()
        dates = [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]
        with self.connection() as connection:
            cutoff = self._learning_overview_cutoff(connection)
            totals_row = connection.execute(
                """WITH latest AS (
                       SELECT item.question_id, item.is_correct
                       FROM session_items item
                       JOIN (
                           SELECT question_id, MAX(id) AS latest_id
                           FROM session_items
                           WHERE question_id IS NOT NULL AND id>?
                           GROUP BY question_id
                       ) chosen ON chosen.latest_id=item.id
                   )
                   SELECT COUNT(q.id) AS total,
                          COUNT(latest.question_id) AS practiced,
                          COALESCE(SUM(CASE WHEN latest.is_correct=1 THEN 1 ELSE 0 END), 0) AS correct
                   FROM questions q
                   LEFT JOIN latest ON latest.question_id=q.id""",
                (cutoff,),
            ).fetchone()
            type_rows = connection.execute(
                """WITH practiced AS (
                       SELECT DISTINCT question_id
                       FROM session_items
                       WHERE question_id IS NOT NULL AND id>?
                   )
                   SELECT q.question_type, COUNT(q.id) AS total,
                          COUNT(practiced.question_id) AS practiced
                   FROM questions q
                   LEFT JOIN practiced ON practiced.question_id=q.id
                   GROUP BY q.question_type""",
                (cutoff,),
            ).fetchall()
            trend_rows = connection.execute(
                """SELECT substr(answered_at, 1, 10) AS answer_date, COUNT(*) AS answer_count
                   FROM session_items
                   WHERE id>? AND substr(answered_at, 1, 10) BETWEEN ? AND ?
                   GROUP BY substr(answered_at, 1, 10)""",
                (cutoff, dates[0].isoformat(), dates[-1].isoformat()),
            ).fetchall()
            recent_rows = connection.execute(
                """SELECT s.id, s.mode, s.started_at, s.completed_at, s.score, s.total,
                          COUNT(item.id) AS answered_count,
                          COALESCE(SUM(item.is_correct), 0) AS correct_count,
                          MAX(item.answered_at) AS last_answered_at
                   FROM sessions s
                   JOIN session_items item ON item.session_id=s.id AND item.id>?
                   GROUP BY s.id
                   ORDER BY last_answered_at DESC, s.id DESC
                   LIMIT 4""",
                (cutoff,),
            ).fetchall()

        total = int(totals_row["total"])
        practiced = int(totals_row["practiced"])
        correct = int(totals_row["correct"])
        totals = {
            "total": total,
            "practiced": practiced,
            "correct": correct,
            "wrong": practiced - correct,
            "unpracticed": total - practiced,
            "progress_percent": int(round(practiced * 100 / total)) if total else 0,
        }
        type_counts = {
            str(row["question_type"]): (int(row["total"]), int(row["practiced"]))
            for row in type_rows
        }
        by_type = []
        for question_type in QuestionType:
            type_total, type_practiced = type_counts.get(question_type.value, (0, 0))
            by_type.append(
                {
                    "question_type": question_type.value,
                    "total": type_total,
                    "practiced": type_practiced,
                    "progress_percent": (
                        int(round(type_practiced * 100 / type_total)) if type_total else 0
                    ),
                }
            )
        trend_counts = {
            str(row["answer_date"]): int(row["answer_count"]) for row in trend_rows
        }
        trend = [
            {"date": item.isoformat(), "count": trend_counts.get(item.isoformat(), 0)}
            for item in dates
        ]
        return {
            "totals": totals,
            "trend": trend,
            "by_type": by_type,
            "recent": [dict(row) for row in recent_rows],
        }

    def count_unmastered_wrong_questions(self) -> int:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM wrong_questions WHERE mastered=0"
            ).fetchone()
        return int(row[0])

    def mark_mastered(self, question_id: int, mastered: bool = True) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE wrong_questions SET mastered=? WHERE question_id=?",
                (int(mastered), question_id),
            )
