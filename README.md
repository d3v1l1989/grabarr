# Grabarr

A simple and efficient tool for managing Sonarr instances.

## 🚀 Features

- 📺 Multiple Sonarr instance management
- 🎯 Simple and intuitive interface
- 💾 SQLite database for data persistence
- 🐳 Docker support for easy deployment
- 🔄 In-memory queue for efficient job processing

## 📋 Requirements

- Python 3.8+
- Docker (optional)
- Sonarr instances to manage

## 🛠️ Installation

### Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/d3v1l1989/grabarr.git
cd grabarr
```

2. Start the application:
```bash
docker-compose up -d
```

### Manual Installation

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

## ⚙️ Configuration

The application uses SQLite for data storage. The database file is automatically created at `./data/grabarr.db`.

## 🐳 Docker Compose Configuration

Here's the default `docker-compose.yml` configuration:

```yaml
version: '3.8'

services:
  api:
    container_name: grabarr-api
    image: ghcr.io/d3v1l1989/grabarr-api:latest
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "8765:8765"
    environment:
      - DATABASE_URL=sqlite:///./data/grabarr.db
    volumes:
      - api_data:/app/data

  frontend:
    container_name: grabarr-frontend
    image: ghcr.io/d3v1l1989/grabarr-frontend:latest
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3456:3456"
    environment:
      - REACT_APP_API_URL=http://localhost:8765
    depends_on:
      - api

volumes:
  api_data:
```

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

## 📦 Using ghcr.io Images

The application's Docker images are available on GitHub Container Registry (ghcr.io):

- API: `ghcr.io/d3v1l1989/grabarr-api:latest`
- Frontend: `ghcr.io/d3v1l1989/grabarr-frontend:latest`

To pull the images:
```bash
docker pull ghcr.io/d3v1l1989/grabarr-api:latest
docker pull ghcr.io/d3v1l1989/grabarr-frontend:latest
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 