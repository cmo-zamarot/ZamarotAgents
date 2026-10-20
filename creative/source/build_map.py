import json, math, sys
d=json.load(open(sys.argv[1]))
LON0,LON1,LAT0,LAT1=34.78,35.02,32.30,32.62
CL=math.cos(math.radians(32.46)); K=11850
def P(lat,lon): return ((lon-LON0)*CL*K, (LAT1-lat)*K)
W=(LON1-LON0)*CL*K; H=(LAT1-LAT0)*K
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=pts[0],pts[-1]; dx,dy=b[0]-a[0],b[1]-a[1]; L=math.hypot(dx,dy) or 1e-9
    i,dm=0,0
    for k,p in enumerate(pts[1:-1],1):
        dd=abs(dy*(p[0]-a[0])-dx*(p[1]-a[1]))/L
        if dd>dm: i,dm=k,dd
    if dm>eps: return rdp(pts[:i+1],eps)[:-1]+rdp(pts[i:],eps)
    return [a,b]
def path(pts,close=False):
    s='M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)
    return s+('Z' if close else '')
E=d['elements']
# coastline chains
segs=[[ (g['lat'],g['lon']) for g in e['geometry']] for e in E if e.get('tags',{}).get('natural')=='coastline']
chains=[]
segs=[s[:] for s in segs]
while segs:
    c=segs.pop(0); changed=True
    while changed:
        changed=False
        for s in segs:
            if s[0]==c[-1]: c+=s[1:]; segs.remove(s); changed=True; break
            if s[-1]==c[0]: c=s+c[1:]; segs.remove(s); changed=True; break
    chains.append(c)
chains.sort(key=len,reverse=True)
main=chains[0]
if main[0][0]<main[-1][0]: main=main[::-1]  # north -> south
pts=[P(*p) for p in main]
pts=rdp(pts,0.8)
x0,y0=pts[0]; xn,yn=pts[-1]
land=[(x0,-200)]+pts+[(xn,H+200),(W+200,H+200),(W+200,-200)]
out={'W':W,'H':H,'land':path(land,True),'coast':path(pts)}
roads={'motorway':[],'trunk':[],'primary':[]}
for e in E:
    t=e.get('tags',{})
    if t.get('highway') in roads:
        roads[t['highway']].append(path(rdp([P(g['lat'],g['lon']) for g in e['geometry']],1.0)))
out['roads']={k:' '.join(v) for k,v in roads.items()}
res=[]
for e in E:
    t=e.get('tags',{})
    if t.get('landuse')=='residential' and e['type']=='way':
        g=[P(q['lat'],q['lon']) for q in e['geometry']]
        if len(g)>3: res.append(path(rdp(g,1.0),True))
out['res']=' '.join(res)
riv=[]
for e in E:
    t=e.get('tags',{})
    if t.get('waterway') and t.get('name') in ('נחל חדרה','נחל אלכסנדר','נחל תנינים'):
        riv.append(path(rdp([P(g['lat'],g['lon']) for g in e['geometry']],0.6)))
out['rivers']=' '.join(riv)
pl={}
for name,(lat,lon) in {'hadera':(32.43699,34.9198258),'olga':(32.4410083,34.88363),'nahal':(32.4644,34.8838),'caesarea':(32.5114971,34.9057861),'netanya':(32.3286181,34.8566246),'orot':(32.4706729,34.8909764),'mikhmoret':(32.4062774,34.8728998)}.items():
    pl[name]=P(lat,lon)
# project zone (schematic): coastal strip north of Givat Olga, south of Nahal Hadera mouth, west of highway 2
zone=[(32.4628,34.8852),(32.4618,34.8985),(32.4470,34.8975),(32.4462,34.8818)]
out['zone']=path([P(*z) for z in zone],True)
zc=[sum(P(*z)[i] for z in zone)/4 for i in (0,1)]
pl['zone']=zc
out['places']=pl
json.dump(out,open(sys.argv[2],'w'))
print(W,H,len(pts),len(out['res']),{k:len(v) for k,v in out['roads'].items()}, pl)
