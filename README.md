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

### Running Tests
```bash
docker-compose exec app pytest
```

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.