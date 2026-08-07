name: Daily Circle Enrollment Update

on:
  schedule:
    # ~10:50 AM IST = 05:20 UTC. Off the exact half-hour mark to avoid
    # GitHub's peak scheduling congestion (:00/:30 are the busiest minutes
    # globally), so it's more likely to fire close to on-time.
    - cron: '20 5 * * *'
  workflow_dispatch: {}   # lets you manually trigger a run from the Actions tab to test

jobs:
  post-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run enrollment update
        env:
          CIRCLE_API_TOKEN: ${{ secrets.CIRCLE_API_TOKEN }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: python enrollment_update.py
