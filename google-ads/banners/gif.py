import sys,glob,os
from PIL import Image
P=sys.argv[1]
for sz in sorted({os.path.basename(f).split('_')[1] for f in glob.glob(f'frames/{P}_*_0.png')}):
    fr=[Image.open(f'frames/{P}_{sz}_{i}.png').convert('RGB') for i in range(4)]
    for colors in (128,96,64,48,32):
        pal=Image.new('RGB',(fr[0].width,fr[0].height*4)); [pal.paste(f,(0,i*f.height)) for i,f in enumerate(fr)]
        pal=pal.quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
        q=[f.quantize(palette=pal,dither=Image.Dither.FLOYDSTEINBERG) for f in fr]
        out=f'out/gif/{P}_{sz}.gif'
        # 4 frames x 2.5s = 10s, loop 3 => 30s total (Google max)
        q[0].save(out,save_all=True,append_images=q[1:],duration=[2500,2500,2500,2500],loop=2,optimize=True)
        kb=os.path.getsize(out)/1024
        if kb<=145: break
    fr[2].save(f'out/gif/{P}_{sz}_static.png',optimize=True)
    print(out, round(kb,1),'KB', colors,'colors')
