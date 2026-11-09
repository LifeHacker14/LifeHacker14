import json,sys,time,re,io,os,urllib.request,urllib.parse
sys.path.insert(0,os.path.dirname(__file__)); from plan import PLAN
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
V=sys.argv[1]; UA={'User-Agent':'LifeHacker14-video-builder/1.0 (documentary research)'}
CF=f'{V}/build/credits.json'
credits={int(k):v for k,v in json.load(open(CF)).items()} if os.path.exists(CF) else {}
def get(u,tries=3):
  for i in range(tries):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=90).read()
    except Exception as e: print(' retry',str(e)[:80],flush=True); time.sleep(20*(i+1))
for i,v in PLAN.items():
  if v[0]!='photo' or (i in credits and os.path.exists(f'{V}/img/{i:02d}.jpg')): continue
  r=get('https://commons.wikimedia.org/w/rest.php/v1/search/page?'+urllib.parse.urlencode(dict(q=v[1]+' filetype:bitmap',limit=8)))
  time.sleep(2)
  ok=False
  for p in (json.loads(r)['pages'] if r else []):
    t=p['title']
    if not re.search(r'\.(jpe?g|png)$',t,re.I): continue
    name=t[5:] if t.startswith('File:') else t
    data=get('https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(name.replace(' ','_')),2); time.sleep(2)
    if not data: continue
    try: im=Image.open(io.BytesIO(data)).convert('RGB')
    except Exception: continue
    if im.width<700: continue
    im.thumbnail((2400,2400)); im.save(f'{V}/img/{i:02d}.jpg',quality=90)
    lic='CC BY-SA 3.0 DE' if name.startswith('Bundesarchiv') else 'see file page'
    credits[i]=dict(title=t,license=lic,url='https://commons.wikimedia.org/wiki/'+urllib.parse.quote(t.replace(' ','_')))
    json.dump(credits,open(CF,'w'),indent=1)
    print(i,t[:80],flush=True); ok=True; break
  if not ok: print(i,'NO RESULT',v[1],flush=True)
print('FINISHED',flush=True)
