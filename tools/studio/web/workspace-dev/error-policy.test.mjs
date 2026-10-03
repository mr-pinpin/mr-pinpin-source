import {shouldReportFailure} from './error-policy.js';
const appURL='http://127.0.0.1:18826/workspace-builds/'+'a'.repeat(64)+'/child.js';
const own=appURL.replace('child.js','chat.js');
let count=0;
function check(label,error,expected,options={}){const actual=shouldReportFailure(error,{appURL,...options});if(actual!==expected)throw Error(label+': '+actual);count++;}
check('MetaMask extension rejection',{message:'Failed to connect to MetaMask',stack:'Error: Failed to connect to MetaMask\n    at connect (chrome-extension://wallet/inpage.js:1:42)'},false);
check('Firefox extension rejection',{stack:'connect@moz-extension://wallet/inpage.js:1:42'},false);
check('own unhandled rejection',{stack:'Error: Render failed\n    at render ('+own+':12:3)'},true);
check('own Firefox stack',{stack:'render@'+own+':12:3'},true);
check('own error filename',null,true,{filename:own});
check('extension filename',null,false,{filename:'chrome-extension://wallet/inpage.js'});
check('message containing app URL',{stack:'Error: Failed '+own+'\n    at connect (chrome-extension://wallet/inpage.js:1:42)'},false);
check('unattributed rejection','Failed to connect to MetaMask',false);
check('another build is not this app',{stack:'Error\n    at x ('+own.replace('a'.repeat(64),'b'.repeat(64))+':1:1)'},false);
check('explicit caught render failure',new Error('render failure'),true,{boundary:'app'});
check('explicit app catch without stack','render failure',true,{boundary:'app'});
console.log(count+' error ownership checks passed');
