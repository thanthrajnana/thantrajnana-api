# thantrajnana-api

## Run API

From the repository root, start the app with:

```bash
uvicorn app.main:app --reload
```

If `uvicorn` is not on `PATH`, use the virtual environment Python:

```bash
./venv/Scripts/python -m uvicorn app.main:app --reload
```

## Database

Make sure `.env` has valid PostgreSQL credentials for your local server:

```env
DATABASE_URL=postgresql://postgres:<your_password>@localhost:5432/thanthrajnana
```