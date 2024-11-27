# Expense Splitter

A web application for splitting expenses among friends and groups, similar to Splitwise.

## Features

- User authentication and authorization
- Create and manage groups
- Add expenses and split them among group members
- Track balances between users
- Settle up payments
- View expense history and statistics

## Tech Stack

### Backend
- Python 3.9+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic for migrations
- JWT authentication

### Frontend
- React
- TypeScript
- Material-UI
- React Query
- React Router

## Getting Started

### Backend Setup
1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start development server:
   ```bash
   npm start
   ```
