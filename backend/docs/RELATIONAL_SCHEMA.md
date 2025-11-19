# Relational Schema (SQLAlchemy)

This backend includes a relational hierarchy to support Subjects → Modules → Lessons → Activities/Quiz and user Progress.

## Entities and Relationships

- Subject (1) → Module (N)
- Module (1) → Lesson (N)
- Lesson (1) → Activity (N)
  - Activity type: `content` or `quiz`
  - For `quiz`, `quiz_questions` JSON contains:
    ```json
    [
      { "question": "...", "options": ["a","b","c","d"], "answerIndex": 0 },
      ...
    ]
    ```
- Progress entries reference lesson/activity completion with optional score

All entities include:
- created_at (server default)
- updated_at (server default, auto-updated)
- is_deleted (soft-delete flag; not enforced by queries unless added)

## Initialization

Tables can be created with:
```bash
python -m src.db.table_init
```

Environment variable:
- SQLALCHEMY_DATABASE_URL (defaults to `sqlite:///./skillmaster.db`)

## Pydantic Schemas

See `src/api/relational_schemas.py` for read and create payload schemas supporting nested reads.
