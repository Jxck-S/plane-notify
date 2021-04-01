def append_airport(filename, airport):
	from PIL import Image, ImageDraw, ImageFont
	distance_mi = airport['distance_mi']
	icao = airport['icao']
	iata = airport['iata_code']
	distance_km = distance_mi * 1.609

	# create Image object with the input image
	image = Image.open(filename)
	# initialise the drawing context with
	# the image object as background
	draw = ImageDraw.Draw(image)

	#Setup fonts
	fontfile = "./dependencies/Roboto-Regular.ttf"
	font = ImageFont.truetype(fontfile, 14)
	mini_font = ImageFont.truetype(fontfile, 12)
	head_font = ImageFont.truetype(fontfile, 16)

	#Setup Colors
	black = 'rgb(0, 0, 0)' # Black
	white = 'rgb(255, 255, 255)' # White
	navish = 'rgb(0, 63, 75)'
	whitish = 'rgb(248, 248, 248)'
	#Info Box
	draw.rectangle(((325, 760), (624, 800)), fill= white, outline=black)
	#Header Box
	draw.rectangle(((401, 738), (549, 760)), fill= navish)
	#ADSBX Logo
	draw.rectangle(((658, 762), (800, 782)), fill= white)
	adsbx = Image.open("./dependencies/ADSBX_Logo.png")
	adsbx = adsbx.resize((25, 25), Image.ANTIALIAS)
	image.paste(adsbx, (632, 757), adsbx)
	#Create Text
	#ADSBX Credit
	(x, y) = (660, 760)
	text = "adsbexchange.com"
	draw.text((x, y), text, fill=black, font=head_font)
	#Nearest Airport Header
	(x, y) = (422, 740)
	text = "Nearest Airport"
	draw.text((x, y), text, fill=white, font=head_font)
	#ICAO | IATA
	(x, y) = (330, 765)
	text = iata + " / " + icao
	draw.text((x, y), text, fill=black, font=font)
	#Distance
	(x, y) = (460, 765)
	text = str(round(distance_mi, 2)) + "mi / " + str(round(distance_km, 2)) + "km away"
	draw.text((x, y), text, fill=black, font=font)
	#Full name
	(x, y) = (330, 783)
	MAX_WIDTH = 325
	if font.getsize(airport['name'])[0] <= MAX_WIDTH:
		text = airport['name']
	else:
		text = ""
		for char in airport['name']:
			if font.getsize(text)[0] >= (MAX_WIDTH - 10):
				text += "..."
				break
			else:
				text += char


	draw.text((x, y), text, fill=black, font=mini_font)
	image.show()
	# save the edited image
	image.save(filename)