import {send} from './bridge.js';
export const renderContext=()=>{};
export const compose=text=>send('compose',{text});
export const showMobile=mode=>{if(mode==='chat')send('focus-conversation');};
