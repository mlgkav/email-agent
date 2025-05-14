# Email CLI Tool

A command-line interface for reading emails using IMAP.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
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
- **flake8**: Lints for syntax and logic issues

To manually run the checks:
```bash
pre-commit run --all-files
```

## Configuration

1. Create a `.env` file in the root directory:
   ```
   IMAP_HOST=imap.gmail.com
   IMAP_USER=your_email@gmail.com
   IMAP_PASSWORD=your_app_password

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key   
   ```

2. For Gmail users, you'll need an App Password:
   - Go to Google Account settings → Security
   - Enable 2-Step Verification if not already done
   - Go to Security → App passwords
   - Generate a new app password and use it as `IMAP_PASSWORD`

3. To get your OpenAI API key:
   - Visit https://platform.openai.com/
   - Sign up or log in to your OpenAI account
   - Go to API Keys section (https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Copy the key immediately (it won't be shown again)
   - Add it to your `.env` file as `OPENAI_API_KEY`

Note: The OpenAI API is a paid service. You'll need to:
   - Add billing information at https://platform.openai.com/account/billing
   - Monitor usage at https://platform.openai.com/usage
   - Free trial credits are available but expire after 3 months

## Usage

List emails from your inbox:
```bash
# List last 10 emails (default)
python3 cli.py list

# List only unread emails
python3 cli.py list --unread

# List specific number of emails
python3 cli.py list --limit 5

# Combine options
python3 cli.py list --unread --limit 5

# Summarize Emails
Summarize emails using GPT-3.5:
```bash
# Summarize last 5 emails (default)
python3 cli.py summarize

# Summarize only unread emails
python3 cli.py summarize --unread

# Summarize specific number of emails
python3 cli.py summarize --limit 3     # summarize last 3 emails

# Combine options (summarize specific number of unread emails)
python3 cli.py summarize --unread --limit 3    # summarize last 3 unread emails
```
