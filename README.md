# Email CLI Tool

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

## Configuration

1. Create a `.env` file in the root directory:
   ```
   IMAP_HOST=imap.gmail.com
   IMAP_USER=your_email@gmail.com
   IMAP_PASSWORD=your_app_password
   ```

2. For Gmail users, you'll need an App Password:
   - Go to Google Account settings → Security
   - Enable 2-Step Verification if not already done
   - Go to Security → App passwords
   - Generate a new app password and use it as `IMAP_PASSWORD`

## Usage

List emails from your inbox:
```bash
# List last 10 emails (default)
python3 cli.py list

# List only unread emails
python3 cli.py list --unread

# List specific number of emails
python3 cli.py list --limit 5
