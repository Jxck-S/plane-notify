import csv
import logging
import os

from pynostr.event import Event
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager
from python_blossom import BlossomClient


def get_blossom_servers():
    """Load blossom servers from CSV file"""
    # Get the directory of this script and look for CSV there
    script_dir = os.path.dirname(__file__)
    csv_file_path = os.path.join(script_dir, "blossom_servers.csv")
    servers = []
    try:
        with open(csv_file_path) as file:
            reader = csv.DictReader(file)
            for row in reader:
                servers.append(row["url"])
    except FileNotFoundError:
        logging.warning("Blossom servers CSV not found at %s", csv_file_path)
    return servers


def get_nostr_relays():
    """Load nostr relays from CSV file"""
    script_dir = os.path.dirname(__file__)
    csv_file_path = os.path.join(script_dir, "nostr_relays.csv")
    relays_list = []

    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"Nostr relays CSV file not found at {csv_file_path}")

    with open(csv_file_path) as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            # Skip empty rows and ensure row has content
            if row and len(row) > 0 and row[0].strip():
                relays_list.append(row[0].strip())

    if not relays_list:
        raise Exception(f"No valid relays found in {csv_file_path}")

    return relays_list


def upload_to_blossom(file_path, private_key):
    """Upload file to blossom server and return URL"""
    servers = get_blossom_servers()

    try:
        client = BlossomClient(private_key, default_servers=servers)

        # Upload the file
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Upload to all blossom servers
        upload_results = client.upload_to_all(
            data=file_data,
        )
        # Get the primary URL (first successful upload)
        primary_url = None
        for server, result in upload_results.items():
            if "url" in result and "error" not in result:
                primary_url = result["url"]
                logging.info("✓ Uploaded to %s: %s", server, primary_url)
                break

        if primary_url:
            return primary_url
        else:
            raise Exception("Failed to upload to any blossom server")

    except Exception as e:
        logging.error("Failed to upload to blossom servers: %s", str(e))
        raise Exception("Failed to upload to any blossom server") from e


def post(message, private_key, image_url=None, reply_to=None):
    relay_manager = RelayManager(timeout=6)
    # Load relay list from CSV
    relays_list = get_nostr_relays()

    relay_manager = RelayManager()
    for relay_url in relays_list:
        relay_manager.add_relay(relay_url)
    relay_manager.run_sync()
    private_key = PrivateKey.from_nsec(private_key)

    if image_url:
        message = f"{message} {image_url}"
    event = Event(message)
    if reply_to:
        event.add_event_ref(reply_to.id)
        event.add_pubkey_ref(reply_to.pubkey)
    event.sign(private_key.hex())

    relay_manager.publish_event(event)
    relay_manager.run_sync()
    relay_manager.close_all_relay_connections()
    return event


def post_with_media(message, file_name, private_key):
    """Upload file using blossom and post to nostr"""
    try:
        if file_name:
            url = upload_to_blossom(file_name, private_key)
            event = post(message, private_key, url)
        else:
            event = post(message, private_key)
        return event
    except Exception as e:
        logging.error("Failed to upload and post: %s", str(e))
        # Fallback to posting without image
        event = post(message, private_key)
        return event
