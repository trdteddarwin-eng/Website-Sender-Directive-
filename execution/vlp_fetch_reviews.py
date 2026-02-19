"""
Fetch Google reviews for all Viva la Pizza locations using Google My Business API.

Usage:
    python3 execution/vlp_fetch_reviews.py

Requires:
    - GMB_ACCOUNT_ID environment variable
    - Google OAuth credentials (token.json or environment variables)
    - google-auth, google-api-python-client packages

Outputs:
    JSON array of new reviews to stdout.
    Stores last_run timestamp in .tmp/vlp_last_review_fetch.json
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Path for storing last run timestamp
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"
LAST_RUN_FILE = TMP_DIR / "vlp_last_review_fetch.json"

# Viva la Pizza location IDs (set via environment or hardcoded after setup)
# Format: comma-separated Google My Business location IDs
# e.g., "locations/1234567890,locations/0987654321,locations/1122334455,locations/5566778899"
LOCATION_IDS_ENV = "VLP_LOCATION_IDS"


def get_credentials():
    """Build Google OAuth credentials from environment or token file."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    # Try environment variables first (Modal / webhook context)
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json:
        token_data = json.loads(token_json)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes", [
                "https://www.googleapis.com/auth/business.manage"
            ]),
        )
    else:
        # Try local token.json file
        token_path = Path(__file__).resolve().parent.parent / "token.json"
        if not token_path.exists():
            logger.error("No credentials found. Set GOOGLE_TOKEN_JSON env var or provide token.json")
            sys.exit(1)

        with open(token_path) as f:
            token_data = json.load(f)

        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes", [
                "https://www.googleapis.com/auth/business.manage"
            ]),
        )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Credentials refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            sys.exit(1)

    return creds


def get_last_run_time():
    """Read the last run timestamp from the state file."""
    if LAST_RUN_FILE.exists():
        try:
            with open(LAST_RUN_FILE) as f:
                data = json.load(f)
            return datetime.fromisoformat(data["last_run"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Could not read last run file: {e}")
    return None


def save_last_run_time(dt: datetime):
    """Save the current run timestamp to the state file."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run": dt.isoformat()}, f)
    logger.info(f"Saved last run time: {dt.isoformat()}")


def get_location_ids():
    """Get the list of Viva la Pizza location IDs."""
    location_ids_raw = os.getenv(LOCATION_IDS_ENV, "")
    if not location_ids_raw:
        logger.error(
            f"{LOCATION_IDS_ENV} environment variable not set. "
            "Set it to a comma-separated list of Google My Business location IDs."
        )
        sys.exit(1)

    location_ids = [lid.strip() for lid in location_ids_raw.split(",") if lid.strip()]
    if not location_ids:
        logger.error(f"No valid location IDs found in {LOCATION_IDS_ENV}")
        sys.exit(1)

    logger.info(f"Found {len(location_ids)} location IDs")
    return location_ids


def fetch_reviews_for_location(service, account_id: str, location_id: str, page_size: int = 50):
    """Fetch all reviews for a single location, handling pagination."""
    all_reviews = []
    next_page_token = None

    # Ensure location_id has proper format
    if not location_id.startswith("locations/"):
        location_id = f"locations/{location_id}"

    parent = f"accounts/{account_id}/{location_id}"

    while True:
        try:
            request_params = {
                "parent": parent,
                "pageSize": page_size,
            }
            if next_page_token:
                request_params["pageToken"] = next_page_token

            response = service.accounts().locations().reviews().list(
                **request_params
            ).execute()

            reviews = response.get("reviews", [])
            all_reviews.extend(reviews)
            logger.info(f"Fetched {len(reviews)} reviews from {location_id} (total so far: {len(all_reviews)})")

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        except Exception as e:
            logger.error(f"Error fetching reviews for {location_id}: {e}")
            break

    return all_reviews


def filter_new_reviews(reviews: list, last_run: datetime = None):
    """Filter reviews to only include those newer than last_run."""
    if last_run is None:
        logger.info("No last run time found. Returning all reviews.")
        return reviews

    new_reviews = []
    for review in reviews:
        create_time_str = review.get("createTime", "")
        if not create_time_str:
            continue

        try:
            # Google API returns ISO 8601 format
            create_time = datetime.fromisoformat(create_time_str.replace("Z", "+00:00"))
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            if create_time > last_run:
                new_reviews.append(review)
        except ValueError as e:
            logger.warning(f"Could not parse review time '{create_time_str}': {e}")
            # Include review if we can't parse the time (safer)
            new_reviews.append(review)

    logger.info(f"Filtered to {len(new_reviews)} new reviews (since {last_run.isoformat()})")
    return new_reviews


def format_review(review: dict, location_id: str) -> dict:
    """Format a raw API review into our standard structure."""
    reviewer = review.get("reviewer", {})
    star_rating = review.get("starRating", "STAR_RATING_UNSPECIFIED")

    # Convert star rating string to integer
    rating_map = {
        "ONE": 1,
        "TWO": 2,
        "THREE": 3,
        "FOUR": 4,
        "FIVE": 5,
        "STAR_RATING_UNSPECIFIED": 0,
    }
    rating = rating_map.get(star_rating, 0)

    return {
        "reviewer_name": reviewer.get("displayName", "Anonymous"),
        "rating": rating,
        "text": review.get("comment", ""),
        "location": location_id,
        "review_id": review.get("reviewId", review.get("name", "")),
        "create_time": review.get("createTime", ""),
        "has_reply": bool(review.get("reviewReply")),
    }


def main():
    """Main entry point: fetch new reviews from all locations and output JSON."""
    from googleapiclient.discovery import build

    account_id = os.getenv("GMB_ACCOUNT_ID", "")
    if not account_id:
        logger.error("GMB_ACCOUNT_ID environment variable not set")
        sys.exit(1)

    # Strip "accounts/" prefix if present
    if account_id.startswith("accounts/"):
        account_id = account_id.replace("accounts/", "", 1)

    location_ids = get_location_ids()
    creds = get_credentials()
    last_run = get_last_run_time()

    # Build the My Business API service
    # Note: Google My Business API v4.9 (mybusinessbusinessinformation is for location info)
    service = build("mybusiness", "v4", credentials=creds, cache_discovery=False)

    all_formatted_reviews = []
    errors = []

    for location_id in location_ids:
        try:
            raw_reviews = fetch_reviews_for_location(service, account_id, location_id)
            new_reviews = filter_new_reviews(raw_reviews, last_run)

            for review in new_reviews:
                formatted = format_review(review, location_id)
                # Skip reviews that already have a reply
                if not formatted["has_reply"]:
                    all_formatted_reviews.append(formatted)
                else:
                    logger.info(f"Skipping already-replied review {formatted['review_id']}")

        except Exception as e:
            error_msg = f"Failed to fetch reviews for location {location_id}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Save current time as last run
    save_last_run_time(datetime.now(timezone.utc))

    # Output results
    output = {
        "reviews": all_formatted_reviews,
        "total_count": len(all_formatted_reviews),
        "locations_queried": len(location_ids),
        "errors": errors,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return output


if __name__ == "__main__":
    main()
