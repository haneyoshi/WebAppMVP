# WebAppMVP
About the project:

My current project is an MVP, or Minimum Viable Product. It's a mini web app designed for a caretaking department to improve communication and coordination between workers, supervisors, and managers. The app provides a clear view of daily operations, including event schedules, attendance tracking, task assignments, and supply requests.

For example, managers can track which workers are present or away in each building and assign tasks accordingly. Workers can submit supply requests directly through the app, and the management team can monitor supply usage across different buildings and analyze monthly consumption. Overall, the app helps streamline operations and improve efficiency within the team.

Tools and Environments:
## 🧱 Tech Stack Overview – EchoTask Web App

This project uses a **React + Flask + SQLite** architecture. Here's a breakdown of what each technology does, why it was chosen, and how they work together.

---

### 🧠 Purpose of This Architecture

The goal of this setup is to keep the project **modular**, **lightweight**, and **easy to maintain**, while still allowing room to grow. This structure also makes it clear how the frontend and backend communicate.

---

## 🛠️ Tools & Technologies

### 1. ⚛️ React (Frontend)
- **Role:** Builds the user interface (UI).
- **Why React?** It’s fast, modular, and great for building dynamic and interactive components (like a search bar, forms, etc.).
- **How it works:** React runs in the browser and interacts with the backend through API calls.

### 2. 🐍 Flask (Backend Framework)
- **Role:** Handles server-side logic and API endpoints.
- **Why Flask?** It's lightweight, beginner-friendly, and flexible. Great for building REST APIs quickly.
- **How it works:** Receives requests from the frontend, processes them, and talks to the database if needed.

### 3. 🐘 SQLite (Database)
- **Role:** Stores application data (users, requests, locations, etc.)
- **Why SQLite?** No setup required, easy to use for local development, and perfect for small-to-medium apps.
- **How it works:** Flask (via SQLAlchemy) interacts with this database to read/write data.

### 4. 🧩 SQLAlchemy (ORM - Object Relational Mapper)
- **Role:** Translates Python code into SQL queries.
- **Why use ORM?** It's cleaner and safer than writing raw SQL, and it makes your code easier to maintain and debug.
- **How it works:** You define models (tables) in Python, and SQLAlchemy handles creating and querying the database tables.

---

## 🔄 How Everything Connects

Here’s how the parts of the app talk to each other:

1. **React** sends an HTTP request (usually via `fetch` or `axios`) to a **Flask** route.
2. **Flask** processes the request, often using data from the **SQLite** database (via SQLAlchemy).
3. Flask returns a **JSON response** back to React.
4. **React** takes that response and updates the UI.

