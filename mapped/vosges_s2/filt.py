import json,sys
held={h[0] for h in json.load(open('held.json'))}
src=sys.argv[1]; out=src.replace('.jsonl','.send.jsonl'); n=0
with open(out,'w') as f:
    for l in open(src):
        o=json.loads(l)
        if o['path'].split('/',1)[1] in held: continue
        f.write(json.dumps(o,separators=(',',':'))+'\n'); n+=1
print(out,n)
