# Organization Search API

A FastAPI application for searching and retrieving organization data from a PostgreSQL database.

## Features

- **Full-Text Search**: Advanced search capabilities using PostgreSQL's text search features
- **REST API**: Simple and intuitive REST API for searching and retrieving organization data
- **Email Authentication**: User signup and verification via email
- **Async Processing**: Fast, non-blocking request handling using async/await
- **Modular Design**: Clean, maintainable code structure with separation of concerns

## Project Structure

```
organization_api/
├── main.py                  # Application entry point
├── .env                     # Environment variables
├── requirements.txt         # Project dependencies
├── app/
│   ├── core/                # Core components
│   │   ├── config.py        # Configuration settings
│   │   ├── database.py      # Database connection handling
│   │   └── email.py         # Email utilities
│   ├── models/              # Data models
│   │   ├── organization.py  # Organization data models
│   │   └── auth.py          # Authentication models
│   ├── api/                 # API endpoints
│   │   ├── endpoints/
│   │   │   ├── search.py    # Search endpoints
│   │   │   ├── organizations.py  # Organization details endpoints
│   │   │   ├── stats.py     # Statistics endpoints 
│   │   │   └── auth.py      # Authentication endpoints
│   │   └── routes.py        # API router configuration
│   └── services/            # Business logic
│       ├── search_service.py    # Search business logic
│       └── auth_service.py      # Auth business logic
```

## Setup and Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- SMTP server access for sending emails

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/organization-search-api.git
cd organization-search-api
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
cp .env.template .env
# Edit .env with your configuration
```

5. **Setup the PostgreSQL database**

First, ensure PostgreSQL is running and create a database:

```bash
sudo -u postgres psql
CREATE DATABASE organization_db;
CREATE USER orguser WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE organization_db TO orguser;
\q
```

6. **Migrate your SQLite data to PostgreSQL (if needed)**

If you have an existing SQLite database, use the migration script:

```bash
python sqlite_to_postgres_migration.py
```

### Running the Application

```bash
python main.py
```

The API will be available at: http://localhost:8000/

API documentation is available at: http://localhost:8000/docs

## API Endpoints

### Search

- `GET /search` - Search for organizations with various filters
  - Query parameters:
    - `name`: Organization name
    - `description`: Description keywords
    - `jurisdiction`: Jurisdiction
    - `legal_form`: Legal form
    - `status`: Status
    - `limit`: Maximum number of results (default: 10)
    - `offset`: Number of results to skip (default: 0)

### Organization Details

- `GET /organization/{org_id}` - Get details for a specific organization
  - Path parameters:
    - `org_id`: Organization ID (openregisters_id)

### Statistics

- `GET /stats` - Get database statistics

### Authentication

- `POST /api/signup` - Sign up for an account
  - Request body:
    - `email`: Email address
    - `first_name`: First name
    - `last_name`: Last name
    - `company`: Company name (optional)

- `POST /api/verify-code` - Verify email access code
  - Request body:
    - `email`: Email address
    - `access_code`: Access code received via email

## Development

### Adding New Endpoints

1. Create a new file in `app/api/endpoints/`
2. Define your endpoint functions using FastAPI Router
3. Add the new router to `app/api/routes.py`

### Environment Variables

The following environment variables can be configured in the `.env` file:

#### Database Configuration
- `PG_HOST`: PostgreSQL host (default: localhost)
- `PG_PORT`: PostgreSQL port (default: 5432)
- `PG_DATABASE`: PostgreSQL database name
- `PG_USER`: PostgreSQL username
- `PG_PASSWORD`: PostgreSQL password

#### Email Configuration
- `SMTP_HOST`: SMTP server host (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP server port (default: 587)
- `SMTP_USERNAME`: SMTP username
- `SMTP_PASSWORD`: SMTP password
- `EMAIL_FROM`: From email address

#### API Configuration
- `DEBUG`: Enable debug mode (default: False)

## Performance Considerations

For optimal performance:

1. **Database Indexes**: Ensure proper indexes are created for search fields
2. **Connection Pooling**: The app uses connection pooling to efficiently manage database connections
3. **Worker Processes**: Adjust the number of worker processes based on your server's CPU cores
4. **PostgreSQL Configuration**: Tune your PostgreSQL server for optimal performance with a large database

## License

[MIT License](LICENSE)
