import requests
import time
import logging
import yaml
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from requests.exceptions import RequestException

def load_config(config_file="config.yaml"):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError("Configuration file is empty")

        return config

    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found")
        sys.exit(1)

    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML syntax: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

config = load_config()

try:
    API_KEY = config["api"]["key"]
    USER = config["api"]["user"]

    if not API_KEY or not str(API_KEY).strip():
        raise ValueError("api.key is empty - check config.yaml")

    if not USER or not str(USER).strip():
        raise ValueError("api.user is empty - check config.yaml")

except KeyError as e:
    print(f"Missing configuration setting: {e}")
    sys.exit(1)

except ValueError as e:
    print(f"Invalid configuration: {e}")
    sys.exit(1)

URL = "http://ws.audioscrobbler.com/2.0/"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_output_filename(base_name="loved_tracks.csv"):
    """
    Prevent overwriting an existing CSV.
    Example:
        loved_tracks.csv
        loved_tracks_20261111_194500.csv
    """
    path = Path(base_name)

    if not path.exists():
        return str(path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{path.stem}_{timestamp}{path.suffix}"


def fetch_loved_tracks(user, api_key):
    loved_tracks = []
    page = 1
    total_pages = 1

    session = requests.Session()

    while page <= total_pages:
        params = {
            "method": "user.getLovedTracks",
            "user": user,
            "api_key": api_key,
            "format": "json",
            "page": page
        }

        try:
            response = session.get(URL, params=params, timeout=30)

            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                logging.error(f"Invalid JSON received on page {page}")
                break

            if "error" in data:
                logging.error(f"API Error: {data.get('message', 'Unknown error')}")
                break

            lovedtracks = data.get("lovedtracks")

            if not lovedtracks:
                logging.error("Missing 'lovedtracks' in API response")
                break

            if page == 1:
                total_pages = int(lovedtracks.get("@attr", {}).get("totalPages", 1))

            for track in lovedtracks.get("track", []):

                track_info = {
                    "title": track.get("name", ""),
                    "artist": track.get("artist", {}).get("name", ""),
                    "url": track.get("url", "")
                }

                loved_tracks.append(track_info)

            logging.info(f"Fetched page {page}/{total_pages}")

            page += 1

            time.sleep(2) # Pause for a bit after every page, so we don't get rate limited.

        except RequestException as e:
            logging.error(f"Network error on page {page}: {e}")

            # Retry once after a short delay
            time.sleep(5)

            try:
                response = session.get(
                    URL,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                logging.info(f"Retry successful for page {page}")

            except Exception:
                logging.error("Retry failed. Stopping.")
                break

    return loved_tracks


def save_tracks(tracks):
    if not tracks:
        logging.warning("No loved tracks found.")
        return

    try:
        df = pd.DataFrame(tracks)

        base_filename = config.get("output", {}).get("file", "loved_tracks.csv")

        filename = get_output_filename(base_filename)

        df.to_csv(filename, index=False, encoding="utf-8")

        logging.info(f"Saved {len(df)} tracks to '{filename}'")

    except PermissionError:
        logging.error("Cannot write CSV file. It may be open in Excel.")

    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")


def main():
    try:
        loved_tracks = fetch_loved_tracks(USER, API_KEY)

        save_tracks(loved_tracks)

    except KeyboardInterrupt:
        logging.warning("Operation cancelled by user.")

    except Exception as e:
        logging.exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()