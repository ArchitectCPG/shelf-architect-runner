  async function refExportRows(){
    if(!db || refBusy) return;
    refBusy = true;
    try{
      refStatus('Reading retail_entries…');
      var snap = await refCall(function(){ return db.collection('retail_entries').get(); });
      var rows = snap.docs.map(function(d){ return Object.assign({ id: d.id }, d.data()); });
      var bundle = { kind: 'shelf_architect_rows', format: 1, exported_at: new Date().toISOString(), count: rows.length, rows: rows };
      var C = (window.claude && typeof window.claude.use === 'function') ? window.claude : null;
      var dl = C ? await C.use('downloads') : null;
      if(!dl){ refStatus('Download is not enabled in this view.'); return; }
      await dl.save({ filename: 'shelf-architect-rows-' + todayISO() + '.json', data: new Blob([JSON.stringify(bundle)], { type: 'application/json' }) });
      refStatus('Exported ' + rows.length + ' rows.');
    }catch(e){
      if(e && e.code === 'declined'){ refStatus(''); return; }
      refStatus('Export failed: ' + (e && e.message ? e.message : e));
    }finally{ refBusy = false; }
  }

