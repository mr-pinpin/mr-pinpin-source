// One page-level sheet; no generated crops or duplicated per-panel illustrations.
export function renderCompactSheets(chapter,selected,{assets,escape}){
 const records=Array.isArray(chapter.studioDraftPreviews)?chapter.studioDraftPreviews.slice(-32):[];
 const current=chapter.studioDraft?.versions?.find(v=>v.version===chapter.studioDraft.currentVersion);
 const applicable=records.filter(r=>r.kind==='compact-sheet'&&Array.isArray(r.panelIds)&&r.panelIds.length&&r.panelIds.every(id=>typeof id==='string')&&Number.isInteger(r.sourceVersion));
 const matching=applicable.filter(r=>r.sourceVersion===selected.version&&r.sourceVersionSHA256===selected.sha256);
 const visible=matching.length?matching:applicable.slice(-1);
 return {sheetAssetIds:new Set(applicable.map(r=>r.assetId)),html:visible.map(r=>{
  const art=assets.find(a=>a.id===r.assetId&&a.sha256===r.assetSHA256);
  const stale=!current||r.sourceVersion!==current.version||r.sourceVersionSHA256!==current.sha256;
  return `<figure data-compact-sheet="${escape(r.assetId)}" data-sheet-stale="${stale}" style="margin:18px 0;padding:16px;border:2px solid ${stale?'#a66':'#8a9'};border-radius:12px"><figcaption><strong>Rough compact sheet · ${escape(r.columns)} columns × ${escape(r.rows)} rows · source v${r.sourceVersion}</strong><p>${stale?'Stale preview: the current narrative differs. Review the saved source version; this sheet does not illustrate the revised text.':'Page-level rough preview of this saved narrative; not finished per-panel artwork.'}</p></figcaption>${art?`<img data-asset-src="${escape(art.url)}" alt="Complete compact storyboard sheet, ${escape(r.panelIds.length)} ordered panels" style="display:block;max-width:100%;max-height:85vh;object-fit:contain">`:'<p>Registered sheet asset is unavailable or its metadata hash differs. No substitute artwork.</p>'}<small>Ordered panels: ${escape(r.panelIds.join(', '))}. Source ${escape(r.sourceVersionSHA256)}. Prompt digest ${escape(r.promptSHA256)}. Receipt digest ${escape(r.receiptSHA256)}. ${escape(r.provenanceStatus)}.</small></figure>`;
 }).join('')};
}
