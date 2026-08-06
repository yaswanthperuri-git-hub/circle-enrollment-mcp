"""
Circle -> Slack daily enrollment update
----------------------------------------
Standalone script (no server, no hosting). Pulls member counts for your
dedicated Circle space groups (batches) and posts a formatted summary to
Slack. Meant to be run by GitHub Actions on a daily cron schedule.

Env vars required (set as GitHub repo secrets):
  CIRCLE_API_TOKEN    - Circle Admin API v2 token
  SLACK_WEBHOOK_URL   - Slack Incoming Webhook URL for the target channel

Edit SPACES below with your actual space group IDs and display names.
Note: these are SPACE GROUP ids (batches/cohorts), not individual space ids.
"""

import os
import sys
import httpx

CIRCLE_API_TOKEN = os.environ["CIRCLE_API_TOKEN"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
CIRCLE_BASE_URL = "https://app.circle.so/api/admin/v2"

# EDIT THIS: your dedicated enrollment batches (label -> Circle access_group_id)
SPACES = {
    "BC16A (Aug - 22,23,24) - IND": 142791,
    "BC17 (Sep 11,12,13) - INTL": 139385,
    "BC18 (Sep 5,6,7) - IND": 142790,
    "BC19 (Sep 19, 20, 21) - IND": 142789,
}


def _headers():
    return {
        "Authorization": f"Bearer {CIRCLE_API_TOKEN}",
        "Content-Type": "application/json",
    }


def get_access_group_member_count(client, access_group_id):
    resp = client.get(
        f"{CIRCLE_BASE_URL}/access_groups/{access_group_id}/community_members",
        params={"page": 1, "per_page": 1},
        headers=_headers(),
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("count", 0)


def build_summary():
    lines = [
        "<@U02FRTNJHSQ> <@U0638PQH6DP>",
        "*Total current enrolments in the below batches:*",
    ]
    with httpx.Client(timeout=30) as client:
        for name, access_group_id in SPACES.items():
            total = get_access_group_member_count(client, access_group_id)
            lines.append(f"{name} : {total}")
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
