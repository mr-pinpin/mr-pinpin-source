const zoomedSheets=new Set();
export function toggleSheetZoom(id){if(zoomedSheets.has(id)){zoomedSheets.delete(id);return false;}if(zoomedSheets.size>=32)zoomedSheets.delete(zoomedSheets.values().next().value);zoomedSheets.add(id);return true;}
// One page-level sheet; no generated crops or duplicated per-panel illustrations.
export function renderCompactSheets(chapter,selected,{assets,escape}){
 const records=Array.isArray(chapter.studioDraftPreviews)?chapter.studioDraftPreviews.slice(-32):[];
 const current=chapter.studioDraft?.versions?.find(v=>v.version===chapter.studioDraft.currentVersion);
 const applicable=records.filter(r=>r.kind==='compact-sheet'&&Array.isArray(r.panelIds)&&r.panelIds.length&&r.panelIds.every(id=>typeof id==='string')&&Number.isInteger(r.sourceVersion));
 const matching=applicable.filter(r=>r.sourceVersion===selected.version&&r.sourceVersionSHA256===selected.sha256);
 const visible=matching.length?matching:applicable.slice(-1);
 return {sheetAssetIds:new Set(applicable.map(r=>r.assetId)),html:visible.map(r=>{
  const art=assets.find(a=>a.id===r.assetId&&a.sha256===r.assetSHA256);
  const zoom=zoomedSheets.has(r.assetId);
  const stale=!current||r.sourceVersion!==current.version||r.sourceVersionSHA256!==current.sha256;
  return `<figure data-compact-sheet="${escape(r.assetId)}" data-sheet-stale="${stale}" style="margin:12px 0;padding:10px;border:2px solid ${stale?'#a66':'#8a9'};border-radius:12px"><figcaption><strong>Rough compact sheet · ${escape(r.columns)} columns × ${escape(r.rows)} rows · source v${r.sourceVersion}</strong><p style="margin:4px 0;font-size:.85em">${stale?`Source v${r.sourceVersion} preview; current v${current?.version??'unknown'}. Review the saved source and current version before using this sheet.`:'Page-level rough preview of this saved narrative; not finished per-panel artwork.'}</p></figcaption><button type="button" data-sheet-zoom aria-pressed="${zoom}">${zoom?'Fit whole page':'Zoom page'}</button>${art?`<img data-asset-src="${escape(art.url)}" alt="Complete compact storyboard sheet, ${escape(r.panelIds.length)} ordered panels" style="display:block;max-width:100%;width:100%;height:${zoom?'auto':'calc(100dvh - 450px)'};min-height:160px;max-height:${zoom?'none':'760px'};object-fit:contain">`:'<p>Registered sheet asset is unavailable or its metadata hash differs. No substitute artwork.</p>'}<details><summary>Source and panel details</summary><small>Ordered panels: ${escape(r.panelIds.join(', '))}. Source ${escape(r.sourceVersionSHA256)}. Prompt digest ${escape(r.promptSHA256)}. Receipt digest ${escape(r.receiptSHA256)}. ${escape(r.provenanceStatus)}.</small></details></figure>`;
 }).join('')};
}
