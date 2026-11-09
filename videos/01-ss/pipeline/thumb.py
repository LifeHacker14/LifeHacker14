import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
V=sys.argv[1]; W,H=1280,720
src=ImageOps.grayscale(Image.open(f'{V}/thumb/himmler.jpg')).convert('RGB')
src=ImageEnhance.Contrast(src).enhance(1.4)
bg=Image.new('RGB',(W,H),(12,12,14))
p=src.resize((int(H*1.2*src.width/src.height),int(H*1.2))).crop((0,0,int(H*1.2*src.width/src.height),H))
mask=Image.linear_gradient('L').rotate(90).resize((p.width,H))  # fade left edge
bg.paste(p,(W-p.width,0),mask)
d=ImageDraw.Draw(bg)
F='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
d.text((60,150),'FROM',font=ImageFont.truetype(F,90),fill=(235,232,225))
d.text((52,240),'8 MEN',font=ImageFont.truetype(F,210),fill=(205,24,32),stroke_width=4,stroke_fill=(0,0,0))
d.rectangle([60,505,520,515],fill=(205,24,32))
bg.save(f'{V}/thumb/thumbnail.jpg',quality=92)
