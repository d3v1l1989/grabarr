# grabarr

A powerful tool for managing multiple Sonarr instances and optimizing search operations.

## Features

- Manage multiple Sonarr instances
- Queue and optimize search operations
- Monitor instance health and status
- Redis caching for improved performance
- GraphQL API for flexible data access

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 16+
- Python 3.9+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/d3v1l1989/grabarr.git
cd grabarr
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3456
- API: http://localhost:8765
- GraphQL Playground: http://localhost:8765/graphql

## Development with GitHub Workspaces

GitHub Workspaces provides a pre-configured development environment. To use it:

1. Navigate to the "Actions" tab in your repository
2. Select the "Development Workspace" workflow
3. Click "Run workflow"
4. Wait for the workspace to be set up
5. Access the development environment through the provided URL

The workspace includes:
- Pre-configured Python and Node.js environments
- Running PostgreSQL and Redis instances
- Hot-reloading development servers
- Database migrations

## Using ghcr.io Images

The application's Docker images are available on GitHub Container Registry (ghcr.io):

- API: `ghcr.io/d3v1l1989/grabarr-api:latest`
- Frontend: `ghcr.io/d3v1l1989/grabarr-frontend:latest`

To pull the images:
```bash
docker pull ghcr.io/d3v1l1989/grabarr-api:latest
docker pull ghcr.io/d3v1l1989/grabarr-frontend:latest
```

## Project Structure

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
├── graphql/              # GraphQL layer
├── docker-compose.yml    # Docker configuration
└── README.md
```

## Development

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Phase 5: Polish & Production Readiness

### 1. Deployment Enhancements
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8765:8765"
    deploy:
      replicas: 3
    depends_on:
      - redis
      - postgres
    
  redis:
    image: redis:alpine
    ports:
      - "7369:7369"
    volumes:
      - redis_data:/data
    
  postgres:
    image: postgres:13
    ports:
      - "6543:6543"
    volumes:
      - pg_data:/var/lib/postgresql/data
    sharding:
      enabled: true
      
  graphql:
    build: ./graphql
    depends_on:
      - api
      
  frontend:
    build: ./frontend
    ports:
      - "3456:3456"
``` 