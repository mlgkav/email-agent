# Email Agent

An intelligent email management tool that uses RAG (Retrieval-Augmented Generation) to help you manage and query your emails effectively.

## Features

- 📧 Email fetching and filtering
- 🤖 Automatic detection of human vs automated emails
- 🔍 Vector-based email storage and retrieval
- 💡 Natural language querying using RAG
- 📊 Beautiful CLI interface with formatted tables

## Requirements

- Python 3.8 or higher
- PostgreSQL 12 or higher with pgvector extension
- Docker (optional, for running PostgreSQL)

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Quality

This project uses pre-commit hooks to maintain code quality:

- **black**: Auto-formats Python code

To manually run the checks:
```bash
pre-commit run --all-files
```

## Configuration

1. Create a `.env` file in the root directory:
   ```
   # Email Configuration
   IMAP_HOST=imap.gmail.com
   IMAP_USER=your_email@gmail.com
   IMAP_PASSWORD=your_app_password

   # Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your_db_password
   DB_NAME=email_agent
   ```

2. For Gmail users, you'll need an App Password:
   - Go to Google Account settings → Security
   - Enable 2-Step Verification if not already done
   - Go to Security → App passwords
   - Generate a new app password and use it as `IMAP_PASSWORD`

3. Set up PostgreSQL with pgvector:
   ```bash
   # Using Docker
   docker run -d \
     --name email-agent-db \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=your_db_password \
     -e POSTGRES_DB=email_agent \
     -p 5432:5432 \
     ankane/pgvector
   ```

## Usage

### List Emails
```bash
# List last 10 emails (default)
python -m email_agent list

# List only unread emails
python -m email_agent list --unread

# List only human emails
python -m email_agent list --human-only

# List specific number of emails
python -m email_agent list --limit 5

# Combine options
python -m email_agent list --unread --human-only --limit 5
```

### Ingest Emails
```bash
# Ingest last 100 emails into vector database
python -m email_agent ingest

# Ingest specific number of emails
python -m email_agent ingest --limit 50
```

### Query Emails
```bash
# Query emails using natural language
python -m email_agent query "Show me emails about project X"

# Limit number of results
python -m email_agent query "Show me emails about project X" --limit 3
```

## Project Structure

```
email_agent/
├── __init__.py          # Package initialization
├── __main__.py         # Entry point
├── core/               # Core email handling
├── storage/            # Vector database storage
├── rag/               # RAG and LLM integration
├── utils/             # Utility functions
└── cli/               # Command-line interface
```

## Development

To install the package in development mode:
```bash
pip install -e .
```

## Testing

Run the test suite:
```bash
python -m pytest
```

## License

MIT License