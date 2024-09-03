To run the program

python main.py (datafilepath) (cache download directory) (output mp4 file) --tags

example 

python main.py data/FL70JZX.txt downloads slideshow.mp4 --zoom -- pan


first argument = data file
second argument = cache folder (folder where all the images will be downloaded)
third argument = output file (must end in mp4)
tags include --zoom to add zoom effects and --pan to add pan effects

example video found in video folder


IMPORTANT
delete download folder if trying to generate a new image or specify a different one.




DEPENDECIES
opencv-python
requests
os
pillow
numpy