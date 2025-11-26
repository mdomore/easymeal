#!/usr/bin/env python3
"""
Simple script to create PWA icons.
Requires: pip install pillow
Run: python3 create_icons.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create 192x192 icon
    img192 = Image.new('RGB', (192, 192), color='#2383e2')
    draw192 = ImageDraw.Draw(img192)
    try:
        # Try to use a system font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        except:
            font = ImageFont.load_default()
    
    text = "E"
    # Get text bounding box
    bbox = draw192.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((192 - text_width) // 2, (192 - text_height) // 2 - 10)
    draw192.text(position, text, fill='white', font=font)
    img192.save('static/icon-192.png')
    print("✓ Created static/icon-192.png")
    
    # Create 512x512 icon
    img512 = Image.new('RGB', (512, 512), color='#2383e2')
    draw512 = ImageDraw.Draw(img512)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 320)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 320)
        except:
            font = ImageFont.load_default()
    
    text = "E"
    bbox = draw512.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((512 - text_width) // 2, (512 - text_height) // 2 - 20)
    draw512.text(position, text, fill='white', font=font)
    img512.save('static/icon-512.png')
    print("✓ Created static/icon-512.png")
    
except ImportError:
    print("Error: Pillow (PIL) is required.")
    print("Install it with: pip install pillow")
    print("\nOr create the icons manually:")
    print("  - static/icon-192.png (192x192 pixels, blue background #2383e2, white 'E')")
    print("  - static/icon-512.png (512x512 pixels, blue background #2383e2, white 'E')")
    exit(1)

