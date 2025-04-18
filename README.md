# Grabarr

A simple and efficient tool for managing Sonarr instances.

## 🚀 Features

- 📺 Multiple Sonarr instance management
- 🎯 Simple and intuitive interface
- 💾 SQLite database for data persistence
- 🐳 Docker support for easy deployment
- 🔄 In-memory queue for efficient job processing

## 📋 Requirements

- Docker and Docker Compose
- Sonarr instances to manage (optional)

## 🛠️ Quick Start with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/d3v1l1989/grabarr.git
cd grabarr
```

2. Configure your environment:
   - Copy `.env.example` to `.env`
   - Update the environment variables in `.env` as needed

3. Start the application:
```bash
docker compose up -d
```

The application will be available at:
- Frontend: http://localhost:3456
- API: http://localhost:8765

## ⚙️ Configuration

The application uses environment variables for configuration. You can configure these in two ways:

1. Through the `.env` file in the root directory
2. Directly in the `docker-compose.yml` file

Here are the available configuration options:

```env
# Application Info
PROJECT_NAME=Grabarr
VERSION=1.0.0
API_V1_STR=/api/v1

# Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# API Key (for simple authentication)
API_KEY=your_api_key_here

# Database
DATABASE_URL=sqlite:///./data/grabarr.db

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8765  # Change this to your API URL in production

# Sonarr (Optional - configure these later)
# SONARR_API_KEY=your_sonarr_api_key
# SONARR_BASE_URL=http://localhost:8989
```

### Production Deployment

For production deployment, make sure to:

1. Set secure values for all sensitive information
2. Update the API URL to point to your production API endpoint
3. Use HTTPS for all API communications
4. Set appropriate CORS settings on the API server

### Docker Compose Services

The application consists of two main services:

1. **API Service** (`grabarr-api`)
   - Port: 8765
   - Environment variables loaded from `.env` file
   - Persistent data stored in `api_data` volume
   - SQLite database stored in `/app/data`

2. **Frontend Service** (`grabarr-frontend`)
   - Port: 3456
   - Depends on the API service
   - Environment variables for API URL configuration

## 🏗️ Project Structure

```
grabarr/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── utils/        # Utility functions
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml    # Docker configuration
└── README.md
```

## 💻 Development

### Manual Installation (Alternative)

If you prefer to run the application without Docker:

1. Clone the repository:
```bash
git clone https://github.com/d3v1l1989/grabarr.git
cd grabarr
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r api/requirements.txt
```

5. Start the application:
```bash
python api/run.py
```

### Backend Development

1. Navigate to the API directory:
```bash
cd api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the development server:
```bash
uvicorn app.main:app --reload --port 8765
```

### Frontend Development

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```