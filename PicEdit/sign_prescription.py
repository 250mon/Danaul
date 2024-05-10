from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


# Open an Image
img = Image.open('원외처방-차트번호5263_1.jpg')

# Call draw method to add 2D graphic in an image
I1 = ImageDraw.Draw(img)

# Custom font style and font size
my_font = ImageFont.truetype('FreeMono.ttf', 65)

# Add text to an image
I1.text((500, 500), "nice care", font=my_font, fill=(255, 0, 0))

# Display edited image
img.show()
