import json,sys
reason=sys.argv[1]; ids=sys.argv[2:]
held=json.load(open('held.json')); new=json.load(open('new.json'))
for i in ids:
    if i in new: new.pop(i); held.append([i,reason])
    else: print('not in new:',i)
json.dump(held,open('held.json','w'),indent=1); json.dump(new,open('new.json','w'),indent=1)
print('held',len(held),'new',len(new))
