"""socials/nostr.py: Interface for posting updates and media to Nostr using relays and Blossom."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path

from pynostr.event import Event
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager
from python_blossom import BlossomClient


def get_blossom_servers() -> list[str]:
    """Load blossom servers from CSV file."""
    # Get the directory of this script and look for CSV there
    script_dir = Path(__file__).parent
    csv_file_path = script_dir / "blossom_servers.csv"
    servers = []
    try:
        with csv_file_path.open() as file:
            reader = csv.DictReader(file)
            for row in reader:
                servers.append(row["url"])
    except FileNotFoundError:
        logging.warning("Blossom servers CSV not found at %s", csv_file_path)
    return servers


def get_nostr_relays() -> list[str]:
    """Load nostr relays from CSV file."""
    script_dir = Path(__file__).parent
    csv_file_path = script_dir / "nostr_relays.csv"
    relays_list = []

    if not csv_file_path.exists():
        msg = f"Nostr relays CSV file not found at {csv_file_path}"
        raise FileNotFoundError(msg)

    with csv_file_path.open() as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            # Skip empty rows and ensure row has content
            if row and len(row) > 0 and row[0].strip():
                relays_list.append(row[0].strip())

    if not relays_list:
        msg = f"No valid relays found in {csv_file_path}"
        raise Exception(msg)

    return relays_list


def upload_to_blossom(file_path: str, private_key: str) -> str:
    """Upload file to blossom server and return URL."""
    servers = get_blossom_servers()

    try:
        client = BlossomClient(private_key, default_servers=servers)

        # Upload the file
        with Path(file_path).open("rb") as f:
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
        msg = "Failed to upload to any blossom server"
        raise Exception(msg)

    except Exception as e:
        logging.exception("Failed to upload to blossom servers: %s", str(e))
        msg = "Failed to upload to any blossom server"
        raise Exception(msg) from e


def post(
    message: str,
    private_key: str,
    image_url: str | None = None,
    reply_to: Event | None = None,
) -> Event:
    """
    Post a note to Nostr relays.

    :param message: The text content of the note.
    :param private_key: User's private key (nsec format).
    :param image_url: URL of media to include (optional).
    :param reply_to: Reference to an event to reply to (optional).
    :return: The signed event object.
    """
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


def post_with_media(message: str, file_name: str | None, private_key: str) -> Event:
    """Upload file using blossom and post to nostr."""
    try:
        if file_name:
            url = upload_to_blossom(file_name, private_key)
            event = post(message, private_key, url)
        else:
            event = post(message, private_key)
        return event
    except Exception as e:
        logging.exception("Failed to upload and post: %s", str(e))
        # Fallback to posting without image
        return post(message, private_key)
