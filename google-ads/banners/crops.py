from PIL import Image
import os
src='img'; out='out/responsive'
# (file, project, name, focal_x 0-1, focal_y 0-1)
items=[('hadera_05.webp','hadera','beach',.5,.6),('hadera_06.webp','hadera','aerial',.45,.5),('hadera_11.webp','hadera','waves',.5,.5),
       ('rehovot_09.webp','rehovot','sunset-aerial',.6,.55),('rehovot_10.webp','rehovot','panorama',.5,.5),
       ('hadera_10.webp','general','founders',.5,.4)]
ratios={'landscape':(1.91,1),'square':(1,1),'portrait':(4,5)}
mins={'landscape':(600,314),'square':(300,300),'portrait':(480,600)}
for f,proj,name,fx,fy in items:
    im=Image.open(os.path.join(src,f)).convert('RGB'); W,H=im.size
    for r,(a,b) in ratios.items():
        tr=a/b
        if W/H>tr: h=H; w=round(H*tr)
        else: w=W; h=round(W/tr)
        x=min(max(round(fx*W-w/2),0),W-w); y=min(max(round(fy*H-h/2),0),H-h)
        c=im.crop((x,y,x+w,y+h))
        # target size, never upscale
        tgt={'landscape':(1200,628),'square':(1200,1200),'portrait':(960,1200)}[r]
        if c.size[0]>tgt[0]: c=c.resize(tgt,Image.LANCZOS)
        if c.size[0]<mins[r][0] or c.size[1]<mins[r][1]: print('skip',proj,name,r,c.size); continue
        p=f'{out}/{proj}_{name}_{r}_{c.size[0]}x{c.size[1]}.jpg'; c.save(p,quality=88); print(p, os.path.getsize(p)//1024,'KB')
