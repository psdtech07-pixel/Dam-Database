#!/usr/bin/env python3
"""
Generate high-fidelity SVG and ICO/PNG logo and favicon for Maharashtra Dam Water Storage.
Minimalist, civic-tech, authoritative dam/reservoir branding.
"""

from PIL import Image, ImageDraw
import os

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <!-- Background Squircle Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="60%" stop-color="#2563eb"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>

    <!-- Reservoir Water Gradient -->
    <linearGradient id="reservoirGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>

    <!-- Spillway Flow Gradient -->
    <linearGradient id="spillwayGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#93c5fd"/>
    </linearGradient>

    <filter id="subtleShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="1.5" stdDeviation="1" flood-opacity="0.25"/>
    </filter>
  </defs>

  <!-- Squircle Base Frame -->
  <rect width="64" height="64" rx="15" fill="url(#bgGrad)"/>
  
  <!-- Subtle Inner Border Highlight -->
  <rect x="1" y="1" width="62" height="62" rx="14" fill="none" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1.5"/>

  <!-- Reservoir Level Wave Lines (Top Storage Basin) -->
  <path d="M12 18 C18 16.5, 24 19.5, 32 18 C40 16.5, 46 19.5, 52 18" 
        stroke="#7dd3fc" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.85"/>
  <path d="M14 23 C20 21.5, 26 24.5, 32 23 C38 21.5, 44 24.5, 50 23" 
        stroke="#bae6fd" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.65"/>

  <!-- Concrete Dam Gravity Wall Structure -->
  <!-- Top Crest Roadway -->
  <rect x="11" y="27" width="42" height="4" rx="1.5" fill="#f8fafc" filter="url(#subtleShadow)"/>

  <!-- Sloping Dam Wall / Spillway Chute Body -->
  <path d="M13 31 L18 48 C22 49, 42 49, 46 48 L51 31 Z" fill="#ffffff" fill-opacity="0.95" filter="url(#subtleShadow)"/>

  <!-- Vertical Spillway Piers / Sluice Gates (3 Sluice Channels) -->
  <rect x="21.5" y="32" width="2.5" height="13" rx="1.2" fill="#1d4ed8"/>
  <rect x="30.75" y="32" width="2.5" height="13" rx="1.2" fill="#1d4ed8"/>
  <rect x="40" y="32" width="2.5" height="13" rx="1.2" fill="#1d4ed8"/>

  <!-- Cascading Flow at Dam Base -->
  <path d="M16 51 C22 49.5, 26 52.5, 32 51 C38 49.5, 42 52.5, 48 51" 
        stroke="url(#spillwayGrad)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  <path d="M20 55 C24 54, 28 56, 32 55 C36 54, 40 56, 44 55" 
        stroke="#60a5fa" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.9"/>
</svg>
'''

# Clean standalone favicon SVG (slightly bolder for 16x16 / 32x32 viewports)
favicon_svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <defs>
    <linearGradient id="favBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
  </defs>
  <rect width="32" height="32" rx="7" fill="url(#favBg)"/>
  
  <!-- Reservoir Wave -->
  <path d="M6 9 C10 8, 14 10, 16 9 C18 8, 22 10, 26 9" stroke="#7dd3fc" stroke-width="1.8" stroke-linecap="round" fill="none"/>
  
  <!-- Dam Wall -->
  <rect x="5" y="13" width="22" height="2.5" rx="1" fill="#ffffff"/>
  <path d="M6.5 15.5 L9.5 25 H22.5 L25.5 15.5 Z" fill="#f1f5f9"/>
  
  <!-- Spillway Gate Divisions -->
  <rect x="11.5" y="16" width="1.6" height="7.5" rx="0.8" fill="#1d4ed8"/>
  <rect x="18.9" y="16" width="1.6" height="7.5" rx="0.8" fill="#1d4ed8"/>
  
  <!-- River Flow -->
  <path d="M8 27 C12 26, 14 28, 16 27 C18 26, 20 28, 24 27" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" fill="none"/>
</svg>
'''

def create_raster_icons():
    # Save SVGs
    with open('web/logo.svg', 'w') as f:
        f.write(svg_content.strip())
    print("✅ Created web/logo.svg")

    with open('web/favicon.svg', 'w') as f:
        f.write(favicon_svg_content.strip())
    print("✅ Created web/favicon.svg")

    # Draw high resolution PNG using PIL for favicon.ico (64x64, 32x32, 16x16)
    sizes = [16, 32, 48, 64, 128, 192, 512]
    images = []

    for sz in sizes:
        img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Scale factor
        s = sz / 64.0

        # Background rounded rect
        radius = int(15 * s)
        # Gradient approximation or rich royal blue
        draw.rounded_rectangle([0, 0, sz - 1, sz - 1], radius=radius, fill=(30, 58, 138, 255))
        # Top gradient wash
        draw.rounded_rectangle([int(1 * s), int(1 * s), sz - int(2 * s), int(32 * s)], radius=radius, fill=(37, 99, 235, 230))
        
        # Reservoir waves
        draw.line([int(12 * s), int(18 * s), int(22 * s), int(16.5 * s), int(32 * s), int(18 * s), int(42 * s), int(16.5 * s), int(52 * s), int(18 * s)], 
                  fill=(125, 211, 252, 230), width=max(1, int(2 * s)))

        # Dam Crest
        draw.rounded_rectangle([int(11 * s), int(27 * s), int(53 * s), int(31 * s)], radius=max(1, int(1.5 * s)), fill=(248, 250, 252, 255))

        # Dam body polygon
        dam_poly = [
            (int(13 * s), int(31 * s)),
            (int(18 * s), int(48 * s)),
            (int(46 * s), int(48 * s)),
            (int(51 * s), int(31 * s))
        ]
        draw.polygon(dam_poly, fill=(255, 255, 255, 245))

        # Spillway Gates
        draw.rounded_rectangle([int(21.5 * s), int(32 * s), int(24 * s), int(45 * s)], radius=max(1, int(1 * s)), fill=(29, 78, 216, 255))
        draw.rounded_rectangle([int(30.75 * s), int(32 * s), int(33.25 * s), int(45 * s)], radius=max(1, int(1 * s)), fill=(29, 78, 216, 255))
        draw.rounded_rectangle([int(40 * s), int(32 * s), int(42.5 * s), int(45 * s)], radius=max(1, int(1 * s)), fill=(29, 78, 216, 255))

        # Base Flow
        draw.line([int(16 * s), int(51 * s), int(24 * s), int(53 * s), int(32 * s), int(51 * s), int(40 * s), int(53 * s), int(48 * s), int(51 * s)],
                  fill=(96, 165, 250, 255), width=max(1, int(2.5 * s)))
        
        images.append(img)
        if sz == 192:
            img.save('web/logo-192.png')
            print("✅ Created web/logo-192.png")
        elif sz == 512:
            img.save('web/logo-512.png')
            print("✅ Created web/logo-512.png")

    # Save multi-resolution favicon.ico
    ico_imgs = [img for img, sz in zip(images, sizes) if sz in [16, 32, 48, 64]]
    ico_imgs[1].save('web/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)], append_images=ico_imgs)
    print("✅ Created web/favicon.ico (16, 32, 48, 64 px)")

if __name__ == '__main__':
    create_raster_icons()
