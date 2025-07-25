# Bearish Keltner Screener

A Flask-based screener using Dhan API for F&O stocks that:
- Scans last 15 daily candles for bearish conditions (Keltner, EMA88, RSI<40)
- Confirms with intraday 1H pullback pattern with RSI behavior
- Sends Telegram alerts if conditions match

## Setup

1. Fill your API keys in `screener.py`
2. Run locally:
```bash
pip install -r requirements.txt
python screener.py
```
3. Or deploy to Render.

Access `/run` endpoint to trigger scan.
