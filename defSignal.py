import requests
import logging
import base64

logger = logging.getLogger('plane-notify.Signal')

def sendSignal(photo, message, config):
    """
    Send a Signal notification with photo and message.

    Supports signal-cli-rest-api format by default.

    Config required:
    [SIGNAL]
    ENABLE = TRUE
    API_URL = http://localhost:8080  # Your Signal API URL
    SENDER = +1234567890              # Sender phone number (with country code)
    RECIPIENTS = +1234567890,+0987654321  # Comma-separated recipient numbers
    """
    sent = False
    retry_count = 0
    max_retries = 4

    try:
        # Get configuration
        api_url = config.get('SIGNAL', 'API_URL').rstrip('/')
        sender = config.get('SIGNAL', 'SENDER')
        recipients_str = config.get('SIGNAL', 'RECIPIENTS')
        recipients = [r.strip() for r in recipients_str.split(',')]

        logger.info(f"Attempting to send Signal message from {sender} to {len(recipients)} recipient(s)")

        # Read and encode the photo
        if isinstance(photo, str):
            # If photo is a file path string
            with open(photo, 'rb') as f:
                photo_data = f.read()
        else:
            # If photo is already a file object
            photo_data = photo.read()
            if hasattr(photo, 'seek'):
                photo.seek(0)  # Reset file pointer for potential reuse

        photo_base64 = base64.b64encode(photo_data).decode('utf-8')

        while not sent and retry_count <= max_retries:
            try:
                # Prepare the payload for signal-cli-rest-api v2 format
                payload = {
                    "message": message,
                    "number": sender,
                    "recipients": recipients,
                    "base64_attachments": [photo_base64]
                }

                # Send the request
                response = requests.post(
                    f"{api_url}/v2/send",
                    json=payload,
                    timeout=30
                )

                if response.status_code == 201 or response.status_code == 200:
                    sent = True
                    logger.info(f"Signal message successfully sent to {len(recipients)} recipient(s)")
                    print("Signal message successfully sent.")
                else:
                    logger.error(f"Signal API returned status code {response.status_code}: {response.text}")
                    print(f"[X] Signal API error: Status {response.status_code}")
                    break

            except requests.exceptions.Timeout:
                retry_count += 1
                logger.warning(f"Signal API timeout (attempt {retry_count}/{max_retries})")
                print(f"Signal timeout count: {retry_count}")
                if retry_count > max_retries:
                    logger.error("Signal attempts exceeded. Message not sent.")
                    print('Signal attempts exceeded. Message not sent.')
                    break

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Cannot connect to Signal API at {api_url}: {str(e)}")
                print(f"[X] Cannot connect to Signal API at {api_url}. Is the Signal API running?")
                break

            except Exception as err:
                logger.error(f"Signal error: {err}", exc_info=True)
                print(f"[X] Unexpected Signal error: {type(err).__name__}: {str(err)}")
                break

    except Exception as e:
        logger.error(f"Signal configuration or setup error: {e}", exc_info=True)
        print(f"[X] Signal configuration error: {str(e)}")
        print("Check your [SIGNAL] configuration in mainconf.ini or plane config")

    return sent
