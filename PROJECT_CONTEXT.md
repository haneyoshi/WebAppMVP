# EchoTask – Project Context

## Overview
EchoTask is an internal web application designed to streamline task coordination and paperwork for cleaners and coordinators.

The system focuses on structured data entry, tracking, and simple workflow management.

---

## Tech Stack
- Frontend: React
- Backend: Flask
- Database: SQLite
- ORM: SQLAlchemy

---

## Core Data Model

### Building
- building_id (PK)
- building_name

### Area
- area_id (PK)
- area_name
- building_id (FK → Building)
- description

Relationship:
- One Building → Many Areas

---

### User
- user_id (PK)
- name
- email
- password_hash
- role (worker | coordinator | supervisor)
- area_id (nullable, FK → Area)

Relationship:
- One Area → One User (worker)
- Coordinators/Supervisors have no area assignment

---

## Key Design Decisions
- Explicit primary keys (e.g., building_id, area_id, user_id)
- area_id is nullable for non-worker roles
- One worker per area (1-to-1 constraint)
- SQLite used for MVP simplicity
- CSV-based seed data for initial setup

---

## Current Progress

### Completed
- Core models (Building, Area, User)
- Database schema
- Seed script with CSV integration

### In Progress
- Backend API development

---

## Current Focus
System validation and setup

- Ensure database initializes correctly
- Verify seed script runs without errors
- Confirm core data (Building, Area, User) is inserted and queryable

---

## Planned Features (MVP)
- Attendance tracking
- Snow log sheets
- Supplies request system
- Event calendar

---

## Constraints / Guidelines
- Use SQLAlchemy ORM (no raw SQL unless necessary)
- Keep naming consistent (e.g., *_id format)
- Keep routes simple and RESTful
- Maintain clear separation between models, routes, and logic

---

## Notes for Development
- Prioritize backend functionality before frontend integration
- Keep implementations simple for MVP
- Focus on clarity over optimization