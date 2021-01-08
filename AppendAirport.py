def download_font():
	import os
	fontfile = "Roboto-Regular.ttf"
	if not os.path.isfile(fontfile):
		print("No font file, downloading now")
		try:
			import requests
			url = 'https://github.com/google/fonts/raw/master/apache/roboto/static/Roboto-Regular.ttf'
			font = requests.get(url)

			open(fontfile, 'wb').write(font.content)
		except:
			raise("Error getting font or storing")
		else:
			print("Successfully got font", fontfile)
	elif os.path.isfile(fontfile):
			print("Already have font, continuing")

def append_airport(filename, icao, airport, distance_mi):
	from PIL import Image, ImageDraw, ImageFont
	distance_km = distance_mi * 1.609

	# create Image object with the input image
	image = Image.open(filename)
	# initialise the drawing context with
	# the image object as background
	draw = ImageDraw.Draw(image)

	#Setup fonts
	fontfile = "Roboto-Regular.ttf"
	font = ImageFont.truetype(fontfile, 14)
	mini_font = ImageFont.truetype(fontfile, 12)
	head_font = ImageFont.truetype(fontfile, 16)

	#Setup Colors
	black = 'rgb(0, 0, 0)' # Black
	white = 'rgb(255, 255, 255)' # White
	navish = 'rgb(0, 63, 75)'
	whitish = 'rgb(248, 248, 248)'
	#Info Box
	draw.rectangle(((316, 760), (605, 800)), fill= white, outline=black)
	#Header Box
	draw.rectangle(((387, 738), (535, 760)), fill= navish)
	#ADSBX Logo
	draw.rectangle(((658, 760), (800, 780)), fill= white)
	adsbx = Image.open('Stealth-48x48.png')
	adsbx = adsbx.resize((25, 25), Image.ANTIALIAS)
	image.paste(adsbx, (632, 757), adsbx)
	#Create Text
	#ADSBX Credit
	(x, y) = (660, 760)
	text = "adsbexchange.com"
	draw.text((x, y), text, fill=black, font=head_font)
	#Nearest Airport Header
	(x, y) = (408, 740)
	text = "Nearest Airport"
	draw.text((x, y), text, fill=white, font=head_font)
	#ICAO
	(x, y) = (320, 765)
	text = icao
	draw.text((x, y), text, fill=black, font=font)
	#Distance
	(x, y) = (432, 765)
	text = str(round(distance_mi, 2)) + "mi / " + str(round(distance_km, 2)) + "km away"
	draw.text((x, y), text, fill=black, font=font)
	#Full name
	(x, y) = (320, 783)
	text = airport[0:56]
	draw.text((x, y), text, fill=black, font=mini_font)
	image.show()
	# save the edited image
	image.save(filename)