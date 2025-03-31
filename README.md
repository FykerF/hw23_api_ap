# URL Shortener API Service

API service for shortening URLs, with analytics and management features.

## Features

### Core Features
- Create, read, update, and delete short links
- Custom aliases for short links
- Link expiration
- Access statistics for links
- User authentication
- Redis caching for popular links

### Additional Features
- Automatic cleanup of unused links
- Search for links by original URL

## API Documentation

### Authentication

#### Register User
```
POST /auth/register
```
Request body:
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Login
```
POST /auth/login
```
Request body:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```
Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Link Management

#### Create Short Link
```
POST /links/shorten
```
Request body:
```json
{
  "original_url": "https://example.com/very/long/url/that/needs/shortening",
  "custom_alias": "mylink",  // Optional
  "expires_at": "2023-12-31T23:59:59"  // Optional
}
```
Response:
```json
{
  "short_code": "mylink",
  "short_url": "https://short.url/mylink",
  "original_url": "https://example.com/very/long/url/that/needs/shortening",
  "created_at": "2023-01-01T12:00:00",
  "expires_at": "2023-12-31T23:59:59"
}
```

#### Get Link Information
```
GET /links/{short_code}
```
Response:
```json
{
  "short_code": "mylink",
  "short_url": "https://short.url/mylink",
  "original_url": "https://example.com/very/long/url/that/needs/shortening",
  "created_at": "2023-01-01T12:00:00",
  "expires_at": "2023-12-31T23:59:59",
  "access_count": 42,
  "last_accessed_at": "2023-01-15T08:30:00"
}
```

#### Update Link
```
PUT /links/{short_code}
```
Request body:
```json
{
  "original_url": "https://example.com/updated/url",
  "expires_at": "2024-06-30T23:59:59"  // Optional
}
```

#### Delete Link
```
DELETE /links/{short_code}
```

#### Get Link Statistics
```
GET /links/{short_code}/stats
```
Response:
```json
{
  "short_code": "mylink",
  "original_url": "https://example.com/very/long/url/that/needs/shortening",
  "created_at": "2023-01-01T12:00:00",
  "access_count": 42,
  "last_accessed_at": "2023-01-15T08:30:00"
}
```

#### Search for Links
```
GET /links/search?original_url=https://example.com
```
Response:
```json
{
  "links": [
    {
      "short_code": "mylink",
      "short_url": "https://short.url/mylink",
      "original_url": "https://example.com/very/long/url/that/needs/shortening",
      "created_at": "2023-01-01T12:00:00"
    }
  ]
}
```

### Redirect
```
GET /{short_code}
```
Redirects to the original URL

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/url-shortener.git
cd url-shortener
```

2. Create an environment file
```bash
cp .env.example .env
```
Edit the `.env` file to configure your environment variables.

3. Build and start the containers
```bash
docker-compose up -d
```

4. Run database migrations
```bash
docker-compose exec app alembic upgrade head
```

5. Access the API at http://localhost:8000

## Development

### Database Migrations
```bash
# Create a new migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Run migrations
docker-compose exec app alembic upgrade head
```

## Database Structure

The service uses PostgreSQL for permanent storage and Redis for caching.

### PostgreSQL Tables
- `users` - User information
- `links` - Link data with original URLs, short codes, and statistics

### Redis Caching
- Short code to URL mappings for fast redirects
- Statistical data for popular links
- Authentication tokens

### Testing

## Testing Structure

The test suite is organized as follows:

```
tests/
├── conftest.py             # Test configuration and fixtures
├── unit/                   # Unit tests
│   ├── test_validators.py  # Test URL and input validation
│   ├── test_auth.py        # Test authentication functions
│   ├── test_shortcode.py   # Test shortcode generation
│   └── test_redis.py       # Test Redis caching functions
├── api/                    # API endpoint tests
│   ├── test_auth.py        # Test auth endpoints
│   ├── test_links.py       # Test link management endpoints
│   ├── test_redirect.py    # Test redirect functionality
│   └── test_errors.py      # Test error handling
├── integration/            # Integration tests
│   ├── test_caching.py     # Test caching integration
│   └── test_cleanup.py     # Test cleanup service
└── load/                   # Load testing
    ├── locustfile.py       # Load testing with Locust
    └── test_performance.py # Performance tests
```

## Test Types

### Unit Tests

Unit tests focus on testing individual functions and classes in isolation. They cover:
- URL and input validation
- Authentication controller functions
- Shortcode generation
- Redis caching operations

### API Tests

These tests verify the behavior of API endpoints, including:
- Link creation, retrieval, update, and deletion
- Authentication (register, login, token validation)
- Redirect functionality
- Error handling

### Integration Tests

Integration tests check how different components work together:
- Caching integration with redirects
- Cleanup service for expired and unused links
- Rate limiting middleware

### Load Tests

Load tests evaluate the performance and stability of the service under load:
- Concurrent link creation and access
- Performance impact of caching
- System behavior with Redis available vs. unavailable

## Running Tests

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- pytest, httpx, pytest-asyncio

### Setup Test Environment

1. Start the services:
```bash
docker-compose up -d
```

2. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests by Category

```bash
# Unit tests only
pytest tests/unit/

# API tests only
pytest tests/api/

# Integration tests only
pytest tests/integration/

# Performance tests only
pytest tests/load/test_performance.py
```

### Run with Coverage

```bash
# Run tests with coverage
coverage run -m pytest

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
```

### Run Load Tests with Locust

```bash
# Start Locust web interface
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Then open http://localhost:8089 in your browser
```

## Performance Testing Results

Performance testing has shown significant improvements when Redis caching is enabled:

- Redirect performance: ~75% faster with caching
- Concurrent requests: ~65% faster with caching
- System can handle ~200 requests/second with minimal latency

## Test Database

Tests use a separate PostgreSQL database (`urlshortener_test`) to avoid interfering with the main application database. The test database is automatically set up and cleaned between test sessions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.