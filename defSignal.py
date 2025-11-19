import requests
import base64

def sendSignal(photo, message, config):
    """
    Send a Signal message with optional photo via signal-cli-rest-api
    
    Args:
        photo: File path to image or None
        message: Text message to send
        config: ConfigParser object with Signal configuration
    
    Returns:
        Boolean indicating success
    """
    sent = False
    retry_c = 0
    
    while sent == False:
        try:
            # Get Signal configuration
            api_url = config.get('SIGNAL', 'API_URL', fallback='http://localhost:8080')
            phone_number = config.get('SIGNAL', 'PHONE_NUMBER')
            recipient = config.get('SIGNAL', 'RECIPIENT')
            
            # Prepare the API request
            url = f"{api_url}/v2/send"
            
            payload = {
                "message": message,
                "number": phone_number,
                "recipients": [recipient]
            }
            
            # Handle photo attachment if provided (TEMPORARILY DISABLED - no maps for now)
            if False: #Disabled change from "False" to "photo" to enable
                try:
                    with open(photo, 'rb') as f:
                        file_data = base64.b64encode(f.read()).decode('utf-8')
                        payload["base64_attachments"] = [file_data]
                except Exception as file_err:
                    print(f"Signal: Error reading image file: {file_err}")
                    raise Exception("No such file or directory")
            
            # Send the request
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if response.status_code == 201:
                sent = True
            else:
                raise Exception(f"API returned status {response.status_code}: {response.text}")
                
        except Exception as err:
            print('err.args:')
            print(err.args)
            print(f"Unexpected {err=}, {type(err)=}")
            print("\nString err:\n"+str(err))
            
            if retry_c > 4:
                print('Signal attempts exceeded. Message not sent.')
                break
            elif 'Connection refused' in str(err):
                print('Signal API connection refused. Is signal-cli-rest-api running?')
                break
            elif 'Timeout' in str(err) or 'timed out' in str(err).lower():
                retry_c += 1
                print('Signal timeout count: '+str(retry_c))
                pass
            elif 'No such file or directory' in str(err):
                print('Signal module couldn\'t find an image to send.')
                break
            elif str(err).startswith('API returned status 4'):
                print('Invalid Signal API configuration or recipient. Message not sent.')
                break
            else:
                print('[X] Unknown Signal error. Message not sent.')
                break
        else:
            print("Signal message successfully sent.")
    
    return sent
