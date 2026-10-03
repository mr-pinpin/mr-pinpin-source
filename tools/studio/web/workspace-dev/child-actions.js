import {send} from './bridge.js';
let actions={};
export function bindActions(value){actions=value;}
export const renderContext=()=>actions.renderContext?.();
export const compose=text=>actions.compose?actions.compose(text):send('compose',{text});
export const showMobile=mode=>actions.showMobile?actions.showMobile(mode):send('focus-conversation');
