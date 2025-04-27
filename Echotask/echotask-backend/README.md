# echotask-backend

echotask-backend/
│
├── app/
│ ├── **init**.py
│ ├── models/ # Database models
│ ├── routes/ # API routes (Blueprints)
│ ├── services/ # Business logic if needed
│ ├── schemas/ # (Optional) for request/response validation
│
├── instance/ # For SQLite DB and instance-specific config
│ └── echotask.db
├── venv # make a mini, isolated environment just for this project
│ └── terminal -> python -m venv venv 
│            └──  -> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 
│               └──  -> .\venv\Scripts\Activate.ps1 
│                   └── -> pip install flask flask-restx python-dotenv
├── .env # Secret config (e.g., keys)
├── config.py # Load settings from .env
├── run.py # App entry point
├── requirements.txt # Dependencies
