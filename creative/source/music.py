import numpy as np, wave
SR=44100; DUR=42.0; N=int(SR*DUR)
rng=np.random.default_rng(7)
t=np.arange(N)/SR
L=np.zeros(N); R=np.zeros(N)
BPM=84; beat=60/BPM; bar=4*beat
def hz(m): return 440*2**((m-69)/12)
# I V vi IV in D: D A Bm G
prog=[[50,57,62,66,69],[45,57,61,64,69],[47,54,62,66,71],[43,55,62,67,71]]
roots=[38,33,35,31]
def env_adsr(n,a,r):
    e=np.ones(n); ai=int(a*SR); ri=int(r*SR)
    if ai>0: e[:ai]=np.linspace(0,1,ai)
    if ri>0: e[-ri:]*=np.linspace(1,0,ri)
    return e
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*SR); 
    if i>=N: return
    n=min(len(sig),N-i); gl=gain*np.sqrt((1-pan)/2); gr=gain*np.sqrt((1+pan)/2)
    L[i:i+n]+=sig[:n]*gl; R[i:i+n]+=sig[:n]*gr
def lowpass(x,fc):
    a=np.exp(-2*np.pi*fc/SR); y=np.zeros_like(x); acc=0.0
    # vectorized one-pole via lfilter-like cumulative approach
    from math import isfinite
    b=1-a
    out=np.empty_like(x); z=0.0
    for k in range(len(x)):
        z=b*x[k]+a*z; out[k]=z
    return out
def level(tt):  # global arrangement intensity
    return np.interp(tt,[0,6,14,21,28.4,35,39,42],[0.55,0.75,0.85,0.95,1.0,0.8,0.7,0.0])
nbars=int(np.ceil(DUR/bar))+1
# PAD
for b in range(nbars):
    st=b*bar; ch=prog[b%4]; n=int((bar+1.2)*SR); tt=np.arange(n)/SR
    sig=np.zeros(n)
    for m in ch:
        f=hz(m+12 if m<50 else m)
        for det in (-0.12,0.0,0.13):
            ff=f*2**(det/12)
            sig+=np.sin(2*np.pi*ff*tt)+0.25*np.sin(4*np.pi*ff*tt)+0.08*np.sin(6*np.pi*ff*tt)
    sig*=env_adsr(n,0.9,1.4)/ (len(ch)*3)
    add(sig,st,0.22,pan=-0.2 if b%2 else 0.2)
# PIANO arpeggio (8ths), from 0.0, pattern up
def piano(f,d=1.6):
    n=int(d*SR); tt=np.arange(n)/SR
    s=sum((0.6**k)*np.sin(2*np.pi*f*(k+1)*tt*(1+0.0004*k))*np.exp(-tt*(2.2+1.3*k)) for k in range(6))
    s*=np.minimum(1,tt/0.004); return s
pat=[0,2,3,4,3,2,1,2]
for b in range(nbars):
    ch=sorted(prog[b%4]); 
    for i in range(8):
        st=b*bar+i*beat/2
        if st>=DUR-1.5: break
        m=ch[pat[i]]+12
        if st<1.0 and i%2: continue
        g=0.11*level(st)*(1.15 if i==0 else 1)
        add(piano(hz(m)),st,g,pan=(i-3.5)/9)
# melody accents at scene starts (bell)
def bell(f,d=3.0):
    n=int(d*SR); tt=np.arange(n)/SR
    return (np.sin(2*np.pi*f*tt)+0.4*np.sin(2*np.pi*f*2.76*tt)*np.exp(-tt*3)+0.2*np.sin(2*np.pi*f*5.4*tt)*np.exp(-tt*6))*np.exp(-tt*1.4)
for st,m in [(0.4,81),(6.2,78),(14.2,81),(21.2,83),(28.4,86),(35.0,81)]:
    add(bell(hz(m)),st,0.07,pan=0.3)
# BASS from 6.2
for b in range(nbars):
    for k in (0,2.5):
        st=b*bar+k*beat
        if st<6.2 or st>DUR-3: continue
        f=hz(roots[b%4]); n=int(beat*1.6*SR); tt=np.arange(n)/SR
        s=np.tanh(1.6*(np.sin(2*np.pi*f*tt)+0.3*np.sin(4*np.pi*f*tt)))*np.exp(-tt*1.4)*np.minimum(1,tt/0.01)
        add(s,st,0.16*level(st))
# KICK soft from 6.2, HATS from 14.2
def kick():
    n=int(0.45*SR); tt=np.arange(n)/SR
    f=48+90*np.exp(-tt*28); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-tt*7)
def hat(d=0.06):
    n=int(d*SR); x=rng.standard_normal(n); x=np.diff(x,prepend=0); return x*np.exp(-np.arange(n)/SR*60)
K=kick()
for i in range(int(DUR/beat)+1):
    st=i*beat
    if 6.2<=st<DUR-4.5 and not (34.3<st<36.4):
        if i%4 in (0,2) or (st>21 and st<34): add(K,st,0.30*level(st))
    if 14.2<=st<DUR-4.5 and not (34.3<st<36.4):
        add(hat(),st+beat/2,0.022*level(st),pan=0.35)
        if st>21.2 and st<34: add(hat(0.03),st+beat/4*3,0.012,pan=-0.35)
# WHOOSH on transitions
def whoosh(d=1.2,up=True):
    n=int(d*SR); x=rng.standard_normal(n); tt=np.arange(n)/SR
    e=np.sin(np.pi*tt/d)**2
    fc=np.linspace(400,5000,n) if up else np.linspace(5000,400,n)
    y=np.zeros(n); z=0.0
    a=np.exp(-2*np.pi*fc/SR)
    for k in range(n): z=(1-a[k])*x[k]+a[k]*z; y[k]=z
    return y*e
for st in (6.2,14.2,21.2,35.0):
    add(whoosh(),st-0.7,0.035,pan=-0.4)
# riser before price + impact
n=int(2.6*SR); tt=np.arange(n)/SR; x=rng.standard_normal(n)
r=np.sin(2*np.pi*np.cumsum(np.linspace(200,900,n))/SR)*0.25+x*0.25
r*=(tt/2.6)**2.2
add(lowpass(r,3000),28.4-2.6,0.12)
imp=np.sin(2*np.pi*np.cumsum(55*np.exp(-np.arange(int(1.5*SR))/SR*2))/SR)*np.exp(-np.arange(int(1.5*SR))/SR*3)
add(imp,28.4,0.35)
# final chord swell
ch=[50,57,62,66,69,74]; n=int(5*SR); tt=np.arange(n)/SR
s=sum(np.sin(2*np.pi*hz(m)*tt) for m in ch)/6*np.minimum(1,tt/1.0)*np.exp(-tt*0.5)
add(s,37.2,0.12)
# REVERB
def reverb(x,dec=2.4,mix=0.28):
    n=int(dec*SR); ir=rng.standard_normal(n)*np.exp(-np.arange(n)/SR*(6.9/dec)); ir/=np.sqrt(np.sum(ir**2))
    m=len(x)+n; F=1<<(m-1).bit_length()
    y=np.fft.irfft(np.fft.rfft(x,F)*np.fft.rfft(ir,F),F)[:len(x)]
    return x*(1-mix)+y*mix*1.4
L=reverb(L); R=reverb(R)
# master: fade in/out, normalize, soft limit
fade=np.minimum(1,t/0.6)*np.clip((DUR-t)/2.5,0,1)
L*=fade; R*=fade
pk=max(np.abs(L).max(),np.abs(R).max()); L/=pk; R/=pk
L=np.tanh(L*1.3)/np.tanh(1.3)*0.8; R=np.tanh(R*1.3)/np.tanh(1.3)*0.8
out=(np.stack([L,R],1)*32767).astype('<i2')
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
print('ok')
