// Global events may originate in browser extensions injected into the app frame.
// Only source locations inside this immutable build establish app ownership.
export function shouldReportFailure(error,{boundary='global',filename='',appURL}={}){
 if(boundary==='app')return true; // An explicit app init/render/route catch.
 let base;try{base=new URL('.',appURL);}catch{return false;}
 const owned=source=>{try{const url=new URL(source);return url.origin===base.origin&&url.pathname.startsWith(base.pathname);}catch{return false;}};
 if(filename&&owned(filename))return true;
 let stack='';try{stack=typeof error?.stack==='string'?error.stack:'';}catch{}
 return stack.split('\n').some(line=>{
  // Ignore the message line: an error mentioning an app URL is not an app frame.
  if(!/^\s*at\s/.test(line)&&!/^\s*[^\s]*@(?:https?:|file:)/.test(line))return false;
  return (line.match(/(?:https?:|file:)\/\/[^\s)]+/g)||[]).some(owned);
 });
}
