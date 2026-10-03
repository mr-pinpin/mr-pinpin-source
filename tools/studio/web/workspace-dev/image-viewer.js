import {asset,readAsset} from './child-state.js';

let current=null;
export function closeImageViewer(){current?.close();}
export async function openImageViewer(id,opener){
 const reference=asset(id);if(!reference)return;
 closeImageViewer();
 const dialog=document.createElement('dialog');dialog.className='asset-viewer';
 const title=document.createElement('strong');title.id='asset-viewer-title';title.textContent=reference.name||'Reference image';
 dialog.setAttribute('aria-labelledby',title.id);
 const toolbar=document.createElement('div');toolbar.className='asset-viewer-toolbar';
 const toggle=document.createElement('button');toggle.type='button';toggle.textContent='Fit to window';toggle.setAttribute('aria-pressed','false');
 const close=document.createElement('button');close.type='button';close.textContent='Close';
 const viewport=document.createElement('div');viewport.className='asset-viewer-viewport';viewport.tabIndex=0;viewport.setAttribute('aria-label','Full-size image; scroll to inspect');
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Loading original image…';
 const image=document.createElement('img');image.alt=reference.name||'Reference image';
 toolbar.append(title,toggle,close);viewport.append(status);dialog.append(toolbar,viewport);document.body.append(dialog);
 let alive=true,url=null;
 const record={close:()=>{if(!alive)return;alive=false;if(url)URL.revokeObjectURL(url);dialog.close();dialog.remove();if(current===record)current=null;if(opener?.isConnected)opener.focus({preventScroll:true});}};
 current=record;close.onclick=record.close;dialog.addEventListener('cancel',event=>{event.preventDefault();record.close();});
 toggle.onclick=()=>{const fit=viewport.classList.toggle('fit');toggle.textContent=fit?'Original size (100%)':'Fit to window';toggle.setAttribute('aria-pressed',String(fit));};
 dialog.showModal();close.focus();
 try{url=await readAsset(reference.url);if(!alive){URL.revokeObjectURL(url);return;}image.src=url;image.onload=()=>{if(!alive)return;status.remove();title.textContent=(reference.name||'Reference image')+` · ${image.naturalWidth} × ${image.naturalHeight} · 100% available`;};image.onerror=()=>{status.textContent='The original image could not be displayed.';};viewport.append(image);}catch(error){if(alive)status.textContent='Image unavailable: '+error.message;}
}

document.addEventListener('click',event=>{const button=event.target.closest?.('[data-open-asset]');if(button)openImageViewer(button.dataset.openAsset,button);});
