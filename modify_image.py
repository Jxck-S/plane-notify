"""
modify_image.py: Image Modification Utility

This module provides functionality to modify images using Pillow (PIL). 
It is primarily used to overlay airport information, credits, and other details onto 
flight tracking map screenshots. It also handles image resizing and cleanup.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import configparser

main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')

fontfile = "./dependencies/Roboto-Regular.ttf"
def append_airport(filename, airport, text_credit=None):
    """
    Overlays airport information and optional credits onto a map screenshot.

    Args:
        filename (str): Base filename of the screenshot (without extension).
        airport (dict): Dictionary containing airport details (name, ICAO, distance, etc.).
        text_credit (str, optional): Text to display in the credit box.
    """
    distance_mi = airport['distance_mi']
    icao = airport['icao']
    iata = airport['iata_code']
    distance_km = distance_mi * 1.609
    if os.path.exists(filename+".png"):
        print("Screenshot image exists modifying image")
        # create Image object with the input image
        image = Image.open(filename+".png")
        print(image)
        # initialise the drawing context with
        # the image object as background
        draw = ImageDraw.Draw(image)

        #Setup fonts
        font = ImageFont.truetype(fontfile, 14)
        mini_font = ImageFont.truetype(fontfile, 12)
        head_font = ImageFont.truetype(fontfile, 16)
        huge_font = ImageFont.truetype(fontfile, 45)

        #Setup Colors
        black = 'rgb(0, 0, 0)' # Black
        white = 'rgb(255, 255, 255)' # White
        navish = 'rgb(0, 63, 75)'
        whitish = 'rgb(248, 248, 248)'
        redish = 'rgb(134, 15, 15)'
        #Info Box
        draw.rectangle(((460, 960+80), (764, 1000+80)), fill= white, outline=black)
        #Header Box
        draw.rectangle(((541, 938+80), (689, 960+80)), fill= redish)

        if text_credit is not None:
            draw.rectangle(((858+80, 962+80), (1000+80, 982+80)), fill= white)
            (x, y) = (860+80, 960+80)
            text = text_credit
            draw.text((x, y), text, fill=black, font=head_font)
        #Nearest Airport Header
        (x, y) = (562, 940+80)
        text = "Nearest Airport"
        draw.text((x, y), text, fill=white, font=head_font)
        #ICAO | IATA
        (x, y) = (470, 965+80)
        if airport['iata_code'] != '' and airport['icao'] != '':
            airport_codes = airport['iata_code'] + " / " + airport['icao']
        elif airport['icao'] != '':
            airport_codes = airport['icao']
        else:
            airport_codes = airport['ident']
        draw.text((x, y), airport_codes, fill=black, font=font)
        #Distance
        (x, y) = (600, 965+80)
        text = str(round(distance_mi, 2)) + "mi / " + str(round(distance_km, 2)) + "km away"
        draw.text((x, y), text, fill=black, font=font)
        #Full name
        (x, y) = (470, 983+80)
        MAX_WIDTH = 325
        if font.getlength(airport['name']) <= MAX_WIDTH:
            text = airport['name']
        else:
            text = ""
            for char in airport['name']:
                if font.getlength(text) >= (MAX_WIDTH - 10):
                    text += "..."
                    break
                else:
                    text += char


        draw.text((x, y), text, fill=black, font=mini_font)
        image.save(filename+".png")
        image = image.convert('RGB')
        reduced_file_name = filename.split(".")[0] + ".jpg"
        image.save(reduced_file_name)
    else:
        print("Screenshot image doesn't exist creating placeholder image")
        # Create a new blank white image with size 1080x1080
        width, height = 1080, 1080
        background_color = "white"
        image = Image.new("RGB", (width, height), background_color)



        # Load the image you want to insert in the middle
        new_image_path = main_config.get('MAP', 'ERROR_LOGO')  # Replace this with the path to your image file
        new_image = Image.open(new_image_path)

        # Calculate new size with the same aspect ratio
        new_width, new_height = new_image.size
        max_size = (width - 20, height - 50)  # Adjust the margins as needed
        new_width, new_height = min(new_width, max_size[0]), min(new_height, max_size[1])
        new_image = new_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate the position to center the new image
        x = (width - new_width) // 2
        y = (height - new_height) // 2

        # Paste the new image onto the existing image
        image.paste(new_image, (x, y))


        # Add text to the image
        draw = ImageDraw.Draw(image)
        text = "Couldn't generate map image, due to loading errors."
        text_color = "black"
        font = ImageFont.truetype(fontfile, 25)  # You can also specify a specific font and size if needed
        text_position = (10, height - 40) 

        draw.text(text_position, text, fill=text_color, font=font)
        # Save as PNG
        image.save(filename+".png", format="PNG")

        # Save as JPG
        image.save(filename+".jpg", format="JPEG")

def reduce_image_size(file_name):
    org_img = Image.open(file_name)
    reduced_file_name = file_name.split(".")[0] + ".jpg"
    reduced_img = org_img.convert('RGB')
    reduced_img.save(reduced_file_name)
    return reduced_file_name
def cleanup_images(path):
    if path:
        for ext in [".png", ".jpg"]:
            try:
                os.remove(path+ext)
            except FileNotFoundError:
                pass