# echotask-backend

echotask-backend/
│
├── app/ # A folder to organize backend server code (Flask)
│ ├── _init_.py
│ ├── models/ # Database models
│ ├── routes/ # API routes (Blueprints)
│ ├── services/ # Business logic if needed
│ ├── schemas/ # (Optional) for request/response validation
│
├── Instance/
│
├── src/ # A "source" code folder for React components, pages, CSS, utilities
│ ├── components/ # reusable components
│   ├── SearchBar.jsx
│   ├── CategoryAccordion.jsx
│   ├── SupplyItem.jsx
│   ├── SummaryPanel.jsx
│
│ ├── pages/ # full pages
│   ├── SuppliesRequestPage.jsx
│
│ ├── App.js # main app entry
│ ├── index.js # React root














src/
├── components/          (reusable components)
│   ├── SearchBar.jsx
│   ├── CategoryAccordion.jsx
│   ├── SupplyItem.jsx
│   ├── SummaryPanel.jsx
│
├── pages/                (full pages)
│   ├── SuppliesRequestPage.jsx
│
├── App.js                (main app entry)
├── index.js              (React root)
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
