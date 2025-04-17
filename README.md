# grabarr

A simple and efficient tool for managing Sonarr instances.

## Features

- Multiple Sonarr instance management
- Simple and intuitive interface
- SQLite database for data persistence
- Docker support for easy deployment

## Requirements

- Python 3.8+
- Docker (optional)
- Sonarr instances to manage

## Installation

### Docker (Recommended)

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings
3. Run `docker-compose up -d`

### Manual Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your settings
6. Run the application: `python run.py`

## Configuration

The application uses environment variables for configuration. Create a `.env` file with the following variables:

```env
DATABASE_URL=sqlite:///./data/grabarr.db
API_KEY=your_api_key_here
```

## Usage

1. Start the application
2. Access the web interface at `http://localhost:3456`
3. Add your Sonarr instances
4. Start managing your Sonarr instances

## Development

### Code Style

The project uses Black for code formatting:

```bash
black .
```

## Development with GitHub Workspaces

GitHub Workspaces provides a pre-configured development environment. To use it:

1. Navigate to the "Actions" tab in your repository
2. Select the "Development Workspace" workflow
3. Click "Run workflow"
4. Wait for the workspace to be set up
5. Access the development environment through the provided URL

The workspace includes:
- Pre-configured Python and Node.js environments
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