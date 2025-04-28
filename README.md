# Tao Dividends API

A production-grade, asynchronous FastAPI service for querying Tao dividends from the Bittensor blockchain, with Redis caching, MongoDB persistence, and background sentiment-based staking/unstaking via Celery. 

## Features
- **Async FastAPI endpoint** to query Tao dividends for a subnet/hotkey
- **Redis caching** (2 min TTL) for blockchain queries
- **Celery background tasks** for Twitter sentiment analysis and stake/unstake
- **MongoDB** for persistent storage
- **Authentication** via API key (header: `X-API-Key`)
- **Dockerized** for easy local or cloud deployment
- **Prometheus & Grafana** for monitoring (optional)
- **Comprehensive tests** with pytest (including concurrency)

---

## Quickstart

### 1. Clone & Configure
```bash
git clone https://github.com/timothywangdev/tao-staking
cd https://github.com/timothywangdev/tao-staking
cp .env.example .env  # Edit with your secrets
```

### 2. Build & Run with Docker Compose
```bash
docker-compose up --build
```
- FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Flower (Celery monitor): [http://localhost:5555](http://localhost:5555)
- MongoDB: localhost:27017
- Redis: localhost:6379

### 3. Run Locally (without Docker)
- Install Python 3.12+
- `pip install -r requirements.txt` (or use `uv pip install -r pyproject.toml --system`)
- Start Redis and MongoDB locally
- Start API:
  ```bash
  uvicorn app.main:app --reload
  ```
- Start Celery worker:
  ```bash
  celery -A app.tasks.sentiment_staking_task worker --loglevel=info
  ```

---

## Environment Variables
Copy `.env.example` and fill in the following (see `app/config.py` for all options):

```
SECRET_KEY=your_api_key_here
BITTENSOR_WALLET_MNEMONIC="..."
DATURA_API_KEY=...
CHUTES_API_KEY=...
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=tao_dividends
REDIS_URL=redis://localhost:6379/1
BITTENSOR_NETWORK=test
DEFAULT_HOTKEY=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v
DEFAULT_NETUID=18
```

---

## API Usage

### GET `/api/v1/tao_dividends`
Query Tao dividends for a subnet/hotkey. Requires `X-API-Key` header.

**Query Parameters:**
- `netuid` (int, optional): Subnet ID (default: 18)
- `hotkey` (str, optional): Account hotkey (default: see config)
- `trade` (bool, optional): If true, triggers background sentiment-based stake/unstake (default: false)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v" -H "X-API-Key: your_api_key_here"
```

**Response:**
```json
{
  "netuid": 18,
  "hotkey": "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v",
  "dividend": 123456789.0,
  "cached": true,
  "stake_tx_triggered": false
}
```

- Returns 401 if API key is missing/invalid
- Returns 503 if blockchain is unavailable
- Returns 500 for internal errors

See [http://localhost:8000/docs](http://localhost:8000/docs) for full OpenAPI docs.

---

## Authentication
All endpoints require an API key via the `X-API-Key` header. Set this to your `SECRET_KEY` from the environment.

---

## Development & Testing

### Linting & Type Checking
```bash
uv pip install -r pyproject.toml --system --extra dev
ruff check .
mypy .
```

### Run Tests
```bash
PYTHONPATH=. pytest tests/ --maxfail=3 --disable-warnings
```
- Includes unit and concurrency tests for API and background tasks

---

## Project Structure
```
app/
  main.py           # FastAPI app entrypoint
  config.py         # Settings & env vars
  api/v1/           # API endpoints
  models/           # Pydantic models
  clients/          # Service clients (bittensor, cache, etc)
  tasks/            # Celery background tasks
  middleware/       # Auth, rate limiting, etc
```

---

## Design Decisions

- **Async everywhere**: All I/O (blockchain, Redis, DB, HTTP) is async for high concurrency
- **Redis**: Used for both caching and as a Celery broker
- **Celery**: Offloads long-running/external API tasks (sentiment, staking)
- **MongoDB**: Async, high-concurrency, persistent storage
- **API Key Auth**: Simple, secure, and easy to rotate
- **Rate Limiting**: Configurable via env vars, prevents abuse
- **Error Handling**: Retries with backoff, logs surfaced via API
- **Security**: All secrets via env vars, never committed
- **Dockerized**: All services containerized for local/cloud
- **Extensible**: Easy to add new background tasks/endpoints
- **Testing**: Pytest for unit, integration, and load; coverage enforced

---

## Implementation Discussion

### Code Structure
- **app/**: Main application code
  - `main.py`: FastAPI entrypoint
  - `config.py`: Centralized settings/env management
  - `api/v1/`: API endpoints and routers
  - `models/`: Pydantic models for validation/serialization
  - `clients/`: Service clients (Bittensor, Redis, MongoDB, etc.)
  - `tasks/`: Celery background tasks (sentiment, staking)
  - `middleware/`: Auth, rate limiting, and other cross-cutting concerns
- **tests/**: Unit, integration, and load tests with fixtures/mocks
- **docker-compose.yml**: Orchestrates API, worker, Redis, MongoDB, and monitoring
- **.env.example**: Example environment config

### Library & Pattern Choices
- **FastAPI**: For async, type-safe, high-performance APIs with automatic docs
- **Celery**: For robust, distributed background task processing
- **Redis**: For low-latency caching and as a Celery broker
- **MongoDB (Motor)**: For async, high-concurrency persistence
- **Pydantic**: For strict data validation and serialization
- **Pytest**: For modern, scalable testing (unit, integration, load)
- **Docker**: For reproducible, isolated local/cloud environments
- **Prometheus/Grafana**: For observability and metrics (optional)
- **Design Patterns**: Dependency injection for testability, separation of concerns (API, services, tasks, models), and clear layering for maintainability

### Tradeoffs & Assumptions
- **Async everywhere**: Chosen for scalability, but requires careful use of async libraries (e.g., Motor, aioredis)
- **MongoDB vs SQL**: MongoDB selected for async support and flexible schema; a SQL DB could be swapped in with minimal changes
- **API Key Auth**: Simpler than OAuth2, but less granular; sufficient for this use case
- **Error handling**: Favor explicit retries and logging over silent failures
- **Testing**: Heavy use of mocks/fixtures for external services to ensure fast, reliable tests
- **Docker-first**: Assumes reviewers will use Docker Compose for fastest onboarding, but local dev is also supported
- **Security**: All secrets/keys must be provided via environment variables; never committed
- **Extensibility**: Designed so new endpoints, background tasks, or integrations can be added with minimal friction

---

## Testing Methodology

- **Unit Tests**: Cover core logic (API, services, models) using pytest and FastAPI's TestClient.
- **Integration Tests**: Test full request/response flow, including cache and DB, using async HTTP clients and test containers/mocks for Redis/MongoDB.
- **End-to-End Tests**: Simulate real user flows, including triggering background tasks and verifying on-chain and sentiment actions.
- **Load/Concurrency Tests**: Use asyncio and pytest to simulate 100+ concurrent requests, ensuring the service remains responsive and correct.
- **Mocking**: All external services (Bittensor, Datura, Chutes) are mocked in tests for reliability and speed.
- **Coverage**: Minimum 85% coverage enforced; critical paths (API, background tasks, caching) are >90%.
- **CI/CD**: Tests are run in CI pipeline on every PR/commit; failures block merges.
- **Fixtures**: Use pytest fixtures for DB, Redis, and external service mocks.
- **How to Run**: `pytest` runs all tests; see `tests/` for structure and examples.

---

## Monitoring
- Flower: [http://localhost:5555](http://localhost:5555) (Celery tasks)
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3000](http://localhost:3000)

---

## Troubleshooting
- Ensure `.env` is filled and present
- Check Docker Compose logs for errors
- For local dev, ensure Redis and MongoDB are running

---

## License
MIT