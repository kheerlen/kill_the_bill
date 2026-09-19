# Kill the Bill

A simple app that reads a receipt image and splits the bill between people — available as a terminal script or a web app.

## Setup

Clone the repository:

```bash
git clone https://github.com/kheerlen/bunq-hackathon-2026.git
cd bunq-hackathon-2026
```

Create a Python 3.11 virtual environment:

```bash
python3.11 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and add your API key.

Example:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Run

Run the terminal app:

```bash
python3.11 main.py
```

Choose the receipt image in `main.py`:

```python
receipt = parse_receipt("assets/medium.jpg")
```

Example images (in `assets/`):

- `easy.png` — English receipt
- `medium.jpg` — receipt with Indian dishes
- `hard.jpg` — receipt completely in Georgian

To use your own image, put it in `assets/` and update the path in `main.py`.

Or run the web app:

```bash
streamlit run web_based.py
```

It opens in your browser at `http://localhost:8501`. Upload a receipt photo,
enter who was there, tick who ate each item, and download the split as JSON.
If `ANTHROPIC_API_KEY` isn't set in `.env`, the app will prompt for it in the browser.

## Project files

- `main.py` — terminal entry point
- `web_based.py` — Streamlit web app entry point
- `terminal/` — modules used only by the terminal app
  - `claude_receipt_parser.py` — parses receipt images
  - `claude_split_bill.py` — splits the bill
  - `contact_list.json` — mock contact list, mimicking phone contacts
- `assets/` — sample receipt images
  - `easy.png` — English receipt example
  - `medium.jpg` — receipt example with Indian dishes
  - `hard.jpg` — receipt example completely in Georgian
- `.env.example` — example environment variables

## Requirements

- Python 3.11
- Anthropic API key
