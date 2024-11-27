# Expense Splitter Application

A full-stack application for splitting expenses among groups of people, built with FastAPI, React, and Supabase.

## Features

- User authentication and authorization
- Create and manage expense groups
- Add and track expenses
- Split expenses equally or custom amounts
- Upload expense receipts
- View balances and suggested settlements
- Profile management with profile pictures

## Prerequisites

- Git
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)
- Supabase account and project
- GitHub account
- Railway account
- Vercel account

## Deployment Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd expense-splitter
```

### 2. Environment Setup

1. Create a `.env` file in the root directory with the following variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_DB_PASSWORD=your_supabase_db_password
DATABASE_URL=your_database_url
JWT_SECRET=your_jwt_secret
```

2. Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Deploy with Docker Compose

The easiest way to deploy both the frontend and backend is using Docker Compose:

```bash
# Build and start the containers
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the containers
docker-compose down
```

The services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 4. Manual Deployment

#### Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Build the Docker image:
```bash
docker build -t expense-splitter-backend .
```

3. Run the container:
```bash
docker run -d \
  -p 8000:8000 \
  --env-file ../.env \
  --name expense-splitter-backend \
  expense-splitter-backend
```

#### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Build the Docker image:
```bash
docker build -t expense-splitter-frontend .
```

3. Run the container:
```bash
docker run -d \
  -p 3000:3000 \
  -e VITE_API_URL=http://localhost:8000 \
  --name expense-splitter-frontend \
  expense-splitter-frontend
```

### 5. Deploy to Railway and Vercel

#### 5.1 Prepare Your Repository

1. Create a new GitHub repository
2. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

#### 5.2 Deploy Backend to Railway

1. Log in to [Railway](https://railway.app/)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository and the backend directory
4. Add the following environment variables in Railway:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_DB_PASSWORD`
   - `DATABASE_URL`
   - `JWT_SECRET`
5. Railway will automatically detect the Dockerfile and deploy
6. Copy the deployment URL for the frontend configuration

#### 5.3 Deploy Frontend to Vercel

1. Log in to [Vercel](https://vercel.com/)
2. Click "New Project" → Import your GitHub repository
3. Select the frontend directory as the root directory
4. Add the following environment variable:
   - `VITE_API_URL`: Your Railway backend URL
5. Deploy the project

#### 5.4 Update CORS Settings

1. In your backend `main.py`, update the CORS origins to include your Vercel domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-domain.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Commit and push the changes:
```bash
git add .
git commit -m "Update CORS settings"
git push
```

### 6. Database Setup

1. Create a new Supabase project
2. Run the database setup script:
```bash
cd backend
python supabase_setup.py
```

## Development Setup

### Backend

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn main:app --reload
```

### Frontend

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

## Database Migrations

The application uses Alembic for database migrations:

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
