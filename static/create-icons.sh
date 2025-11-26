#!/bin/bash
# Simple icon creation using ImageMagick or fallback
if command -v convert &> /dev/null; then
    # Create 192x192 icon
    convert -size 192x192 xc:#2383e2 -gravity center -pointsize 100 -fill white -annotate +0+0 "E" icon-192.png
    # Create 512x512 icon
    convert -size 512x512 xc:#2383e2 -gravity center -pointsize 300 -fill white -annotate +0+0 "E" icon-512.png
    echo "Icons created with ImageMagick"
elif command -v magick &> /dev/null; then
    magick -size 192x192 xc:#2383e2 -gravity center -pointsize 100 -fill white -annotate +0+0 "E" icon-192.png
    magick -size 512x512 xc:#2383e2 -gravity center -pointsize 300 -fill white -annotate +0+0 "E" icon-512.png
    echo "Icons created with ImageMagick"
else
    echo "ImageMagick not found. Icons will need to be created manually."
    echo "Create icon-192.png (192x192) and icon-512.png (512x512) with blue background (#2383e2) and white 'E'"
fi
