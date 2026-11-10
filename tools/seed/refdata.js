
  // ---------- Reference data: export from main, seed a new instance (SOP v85 build 3, seed_by_page) ----------
  // The reference set is Steve's general reference, never client data. Export runs in the main instance and saves
  // one JSON bundle; a new instance is published with that bundle at seed/reference_set.json and the Seed action
  // writes it into the instance's own database. Existing docs are merged (main is the source), never deleted.
  var REF_SET = {
    collections: [
      { name: 'retailers' },
      { name: 'review_calendar' },
      { name: 'category_scan' },
      { name: 'distributors' },
      { name: 'insights', where: ['client_id', '==', 'general'] }
    ],
    docs: [
      'app_meta/dropdowns', 'app_meta/platform_bridge', 'app_meta/foot_traffic', 'app_meta/acv_adjusted',
      'app_meta/store_locations', 'app_meta/pull_process', 'app_meta/pull_process_core',
      'app_meta/onboarding_runbook', 'app_meta/pull_prompt_template',
      'forecast_images/retail-marketing-framework', 'pull_matrix/_template'
    ]
  };
  var REF_SEED_URL = 'seed/reference_set.json';
  var refSeedBundle = null, refSeedArmed = false, refBusy = false;

  function refStatus(msg){ var el = document.getElementById('refStatus'); if(el) el.textContent = msg || ''; }
  function refSleep(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
  async function refCall(fn){
    for(var a = 0; a < 6; a++){
      try{ return await fn(); }
      catch(e){
        var c = e && e.code;
        if((c === 'resource_exhausted' || c === 'unavailable') && a < 5){ await refSleep(800 * (a + 1) + Math.random() * 400); continue; }
        throw e;
      }
    }
  }

  async function refExport(){
    if(!db || refBusy) return;
    refBusy = true;
    try{
      var out = [], counts = {}, sop = null;
      for(var i = 0; i < REF_SET.collections.length; i++){
        var c = REF_SET.collections[i], q = db.collection(c.name);
        if(c.where) q = q.where(c.where[0], c.where[1], c.where[2]);
        refStatus('Reading ' + c.name + '…');
        var snap = await refCall(function(){ return q.get(); });
        counts[c.name] = snap.size;
        snap.docs.forEach(function(d){ out.push({ path: c.name + '/' + d.id, data: d.data() }); });
      }
      for(var j = 0; j < REF_SET.docs.length; j++){
        var p = REF_SET.docs[j];
        var s = await refCall(function(){ return db.doc(p).get(); });
        if(s.exists){ out.push({ path: p, data: s.data() }); counts[p] = 1; if(p === 'app_meta/pull_process') sop = (s.data() || {}).version || null; }
        else counts[p] = 0;
      }
      var bundle = { kind: 'shelf_architect_reference_set', format: 1, exported_at: new Date().toISOString(),
        sop_version: sop, counts: counts, doc_count: out.length, docs: out };
      var C = (window.claude && typeof window.claude.use === 'function') ? window.claude : null;
      var dl = C ? await C.use('downloads') : null;
      if(!dl){ refStatus('Download is not enabled in this view.'); return; }
      refStatus('Saving ' + out.length + ' docs…');
      await dl.save({ filename: 'shelf-architect-reference-set-' + todayISO() + '.json',
        data: new Blob([JSON.stringify(bundle)], { type: 'application/json' }) });
      refStatus('Exported ' + out.length + ' docs.');
    }catch(e){
      if(e && e.code === 'declined'){ refStatus(''); return; }
      refStatus('Export failed: ' + (e && e.message ? e.message : e));
    }finally{ refBusy = false; }
  }

  async function refSeedRun(){
    if(!db || !refSeedBundle || refBusy) return;
    refBusy = true;
    var docs = refSeedBundle.docs || [], made = 0, merged = 0, failed = [];
    try{
      for(var i = 0; i < docs.length; i++){
        var it = docs[i];
        if(i % 10 === 0) refStatus('Seeding ' + (i + 1) + ' of ' + docs.length + '…');
        try{
          var ref = db.doc(it.path);
          var snap = await refCall(function(){ return ref.get(); });
          if(snap.exists){ await refCall(function(){ return ref.update(it.data); }); merged++; }
          else { await refCall(function(){ return ref.set(it.data); }); made++; }
        }catch(e){ failed.push(it.path + ': ' + ((e && (e.code || e.message)) || e)); }
      }
      var pc = db.doc('app_meta/pull_conflicts');
      var pcs = await refCall(function(){ return pc.get(); });
      if(!pcs.exists){
        await refCall(function(){ return pc.set({ client_id: '', entries: [],
          name: 'Pull conflict log, this instance (write-side events only)',
          rule: 'Append-only log of write-side conflicts for this client: skipped_overwrite and overwrite_detected. Entry shape {at, type, job, client_id, profile, block, kept, dropped, note}. Lease events go to the main instance. Keep the newest 200. Set client_id at intake.',
          set_by: 'Seed reference data action, ' + todayISO(), updated: todayISO() }); });
        made++;
      }
      await refCall(function(){ return db.doc('app_meta/seed_log').set({
        last_run: new Date().toISOString(), bundle_exported_at: refSeedBundle.exported_at || null,
        bundle_sop_version: refSeedBundle.sop_version || null, bundle_doc_count: docs.length,
        bundle_counts: refSeedBundle.counts || {}, created: made, merged: merged,
        failed_count: failed.length, failed: failed.slice(0, 50) }); });
      refStatus('Seeded: ' + made + ' new, ' + merged + ' merged' + (failed.length ? ', ' + failed.length + ' failed (see app_meta/seed_log)' : '') + '.');
      var b = document.getElementById('seedBanner'); if(b && !failed.length) b.style.display = 'none';
    }catch(e){
      refStatus('Seed stopped: ' + (e && e.message ? e.message : e));
    }finally{ refBusy = false; refSeedArmed = false; var btn = document.getElementById('refSeed'); if(btn) btn.textContent = 'Seed reference data'; }
  }

  function refSeedClick(){
    if(refBusy || !refSeedBundle) return;
    var n = (refSeedBundle.docs || []).length;
    if(!refSeedArmed){
      refSeedArmed = true;
      this.textContent = 'Tap again to write ' + n + ' docs';
      var me = this; setTimeout(function(){ if(refSeedArmed && !refBusy){ refSeedArmed = false; me.textContent = 'Seed reference data'; } }, 8000);
      return;
    }
    refSeedRun();
  }

  async function refDataInit(){
    var ex = document.getElementById('refExport'), sd = document.getElementById('refSeed'), bn = document.getElementById('seedBanner');
    if(ex) ex.addEventListener('click', refExport);
    if(sd) sd.addEventListener('click', refSeedClick);
    if(bn) bn.addEventListener('click', function(e){ if(e.target && e.target.id === 'seedBannerBtn') refSeedClick.call(document.getElementById('refSeed')); });
    try{
      var r = await fetch(REF_SEED_URL, { cache: 'no-store' });
      if(!r.ok) return;
      var b = await r.json();
      if(!b || b.kind !== 'shelf_architect_reference_set' || !Array.isArray(b.docs)) return;
      refSeedBundle = b;
    }catch(e){ return; }
    if(sd) sd.hidden = false;
    try{
      var probe = await refCall(function(){ return db.collection('retailers').limit(1).get(); });
      if(probe.empty && bn){
        bn.innerHTML = 'This instance has no reference data yet (' + refSeedBundle.docs.length + ' docs ready, exported ' +
          esc(String(refSeedBundle.exported_at || '').slice(0, 10)) + '). <button class="primary-btn" id="seedBannerBtn" type="button">Seed reference data</button>';
        bn.style.display = 'block';
      }
    }catch(e){}
  }

