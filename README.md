# Data Migration Service

## Overview

The Data Migration Service is responsible for coordinating complex database migrations across sharded MongoDB and PostgreSQL databases while maintaining system integrity and performance.

## Features

- Standalone service for coordinating database migrations
- Support for sharded database topologies (MongoDB and PostgreSQL)
- Minimized downtime and performance impact during migrations
- Monitoring and rollback capabilities
- Integration with MCP, Chat, and Adaptor services

## Setup Development Environment

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Poetry (for dependency management)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/data-migration-service.git
   cd data-migration-service
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t data-migration-service .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env data-migration-service
   ```

## API Documentation

Once the service is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Project Structure

```
data-migration-service/
│
├── README.md
├── pyproject.toml
├── setup.py
├── Dockerfile
├── .env.example
├── .gitignore
│
├── migrations/
│   ├── schema/
│   │   ├── mongodb/
│   │   └── postgres/
│   └── data/
│       ├── mongodb/
│       └── postgres/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   ├── security.py
│   │   └── metrics.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── endpoints/
│   │   ├── models/
│   │   └── dependencies.py
│   │
│   ├── coordinator/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── orchestrator.py
│   │   ├── scheduler.py
│   │   ├── status_tracker.py
│   │   └── validation.py
│   │
│   ├── shard/
│   │   ├── __init__.py
│   │   ├── topology.py
│   │   ├── router.py
│   │   ├── consistency.py
│   │   └── balancer.py
│   │
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── mongodb.py
│   │   ├── postgres.py
│   │   ├── batch.py
│   │   └── parallel.py
│   │
│   ├── transformers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── message.py
│   │   ├── tenant.py
│   │   ├── channel.py
│   │   └── factory.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── postgres.py
│   │   └── mongodb.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── migration_service.py
│   │   ├── status_service.py
│   │   ├── backup_service.py
│   │   └── monitoring_service.py
│   │
│   ├── message_broker/
│   │   ├── __init__.py
│   │   ├── publisher.py
│   │   ├── consumer.py
│   │   ├── rabbitmq.py
│   │   └── kafka.py
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── mcp_client.py
│   │   ├── chat_client.py
│   │   └── adaptor_client.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── database.py
│       ├── retry.py
│       ├── validation.py
│       ├── async_utils.py
│       └── monitoring.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── tools/
│   ├── shard_simulator.py
│   ├── performance_analyzer.py
│   ├── migration_generator.py
│   └── status_dashboard/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── migrations/
│   └── operations/
│
└── k8s/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── secrets.yaml
```

## Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run with coverage report
pytest --cov=app
```

## License

Proprietary - All Rights Reserved