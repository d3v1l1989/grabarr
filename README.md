# Sonarr Grabarr - Project Plan

## Phase 1: Core Foundation (MVP)

### Infrastructure Setup
- Docker Compose configuration with services:
  * API Service (FastAPI) - Port 8765
  * Redis (for caching and queuing) - Port 7369
  * PostgreSQL (main database) - Port 6543
  * GraphQL API layer
  * Frontend (React + TypeScript) - Port 3456

### Basic Features
1. Sonarr Instance Management:
   * CRUD operations for instances
   * Connection testing with retry logic
   * Basic configuration storage

2. Core Data Layer:
   * Database schema design (grabarr database)
   * Redis cache implementation
   * Basic GraphQL schema

3. Simple Web UI:
   * Instance management interface
   * Basic status display
   * Authentication system

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
git clone https://github.com/yourusername/grabarr.git
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