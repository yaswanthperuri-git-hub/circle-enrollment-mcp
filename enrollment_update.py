"""
Circle -> Slack daily enrollment update
----------------------------------------
Standalone script (no server, no hosting). Pulls member counts and new
joins for your dedicated Circle spaces and posts a formatted summary to
Slack. Meant to be run by GitHub Actions on a daily cron schedule.

Env vars required (set as GitHub repo secrets):
  CIRCLE_API_TOKEN    - Circle Admin API v2 token
  SLACK_WEBHOOK_URL   - Slack Incoming Webhook URL for the target channel

Edit SPACES below with your actual space IDs and display names.
"""

import os
import sys
import datetime
import httpx

CIRCLE_API_TOKEN = os.environ["CIRCLE_API_TOKEN"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
CIRCLE_BASE_URL = "https://app.circle.so/api/admin/v2"

# EDIT THIS: your dedicated enrollment spaces (name -> Circle space_id)
SPACES = {
    "BC16A": 1133995,
    "BC17": 1121445,
    "BC18": 1133998,
    "BC19": 1134000,
}

LOOKBACK_HOURS = 24


def _headers():
    return {
        "Authorization": f"Bearer {CIRCLE_API_TOKEN}",
        "Content-Type": "application/json",
    }


def fetch_space_members_page(client, space_id, page=1, per_page=100):
    resp = client.get(
        f"{CIRCLE_BASE_URL}/spaces/{space_id}/space_members",
        params={"page": page, "per_page": per_page},
        headers=_headers(),
    )
    resp.raise_for_status()
    return resp.json()


def get_total_members(client, space_id):
    data = fetch_space_members_page(client, space_id, page=1, per_page=1)
    return data.get("count", 0)


def get_new_members_count(client, space_id, hours=LOOKBACK_HOURS):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    new_count = 0
    page = 1
    while True:
        data = fetch_space_members_page(client, space_id, page=page, per_page=100)
        records = data.get("records", [])
        if not records:
            break
        stop = False
        for m in records:
            created_at_raw = m.get("created_at")
            if not created_at_raw:
                continue
            created_at = datetime.datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
            if created_at >= cutoff:
                new_count += 1
            else:
                stop = True  # records assumed newest-first; safe to stop early
        if stop or not data.get("has_next_page"):
            break
        page += 1
    return new_count


def build_summary():
    lines = ["*Total current enrolments in the below batches:*"]
    with httpx.Client(timeout=30) as client:
        for name, space_id in SPACES.items():
            total = get_total_members(client, space_id)
            new = get_new_members_count(client, space_id)
            lines.append(f"• {name}: {total} total ({new} new registrations in last {LOOKBACK_HOURS}h)")
    return "\n".join(lines)


def post_to_slack(text):
    resp = httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=15)
    resp.raise_for_status()


def main():
    summary = build_summary()
    print(summary)  # shows up in the GitHub Actions run log too
    post_to_slack(summary)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
