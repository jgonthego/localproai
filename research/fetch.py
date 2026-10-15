import re,html,json,subprocess,concurrent.futures as cf
def get(line):
    n,u=line.split('|')
    try:r=subprocess.run(['curl','-sL','-m','20','-A','Mozilla/5.0 (X11; Linux x86_64) Chrome/124','-w','\n%{http_code}',u],capture_output=True,text=True,errors='ignore').stdout
    except Exception as e: return n,u,0,'',[]
    body,code=r.rsplit('\n',1)
    t=re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>',' ',body);title=re.search(r'(?is)<title>(.*?)</title>',body)
    t=html.unescape(re.sub(r'<[^>]+>',' ',t));t=re.sub(r'\s+',' ',t)
    p=re.findall(r'.{0,50}\$\s?\d[\d,.]*.{0,40}',t)
    return n,u,code,(title.group(1).strip()[:80] if title else ''),p[:6]
L=[l.strip() for l in open('cands.txt') if l.strip()]
with cf.ThreadPoolExecutor(20) as ex: res=list(ex.map(get,L))
json.dump(res,open('raw.json','w'),indent=1)
for n,u,c,ti,p in res: print(n,c,ti,'||',' ## '.join(p[:3])[:300])
