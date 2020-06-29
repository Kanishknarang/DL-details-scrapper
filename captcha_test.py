from PIL import Image
from scipy.ndimage.filters import gaussian_filter
import numpy
import pytesseract
from PIL import ImageFilter
import cv2



img = Image.open("captcha_original.png")
gray = img.convert('L')
gray.save('captcha_gray.png')
bw = gray.point(lambda x: 0 if x < 1 else 255, '1')
bw.save('captcha_thresholded.png')

img = cv2.imread('captcha_thresholded.png', cv2.IMREAD_GRAYSCALE)
cv2.dilate(img,(5,5),img)

text = pytesseract.image_to_string(img, config = '--psm 7')

final_text = ''
for character in text:
    if character.isalnum():
        final_text+=character
print(final_text)