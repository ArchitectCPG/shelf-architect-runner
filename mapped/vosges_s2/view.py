import json,sys
for i,l in enumerate(open(sys.argv[1]),1):
    o=json.loads(l); d=o['data']
    print(i, o['path'].split('/',1)[1], '|', d.get('brand'), '|', d.get('product_name'), '|', d.get('size_oz'), d.get('count'), '|', d.get('price'), '|', d.get('block').split('/')[1], '|', d.get('pricing_cohort',''))
