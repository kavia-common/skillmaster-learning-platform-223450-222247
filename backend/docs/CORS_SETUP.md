# CORS Setup (FastAPI)

Ensure the frontend at http://localhost:3000 can call the backend at http://localhost:3001 with credentials.

1) Configure FastAPI CORS in `src/api/main.py` (already present in this repo). Validate the following:
- allow_origins includes `http://localhost:3000`
- allow_credentials is True
- allow_methods and allow_headers include `*` or required headers

Example:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2) Environment variable:
Set `FRONTEND_ORIGIN=http://localhost:3000` in `.env`.

3) Verify:
- Start backend: `uvicorn src.api.main:app --port 3001 --reload`
- Open http://localhost:3001 and inspect response headers contain:
  - `access-control-allow-origin: http://localhost:3000`
  - `access-control-allow-credentials: true`
