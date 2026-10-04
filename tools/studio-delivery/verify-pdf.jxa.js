// macOS system PDFKit verifier; JXA uses installed frameworks, no compiler/package.
function run(args){
 ObjC.import('Foundation');ObjC.import('PDFKit');
 if(args.length!==2)throw Error('Usage: osascript -l JavaScript verify-pdf.jxa.js PDF MANIFEST');
 const doc=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(args[0]));if(!doc)throw Error('Invalid PDF');
 const raw=$.NSString.stringWithContentsOfFileEncodingError(args[1],$.NSUTF8StringEncoding,null),manifest=JSON.parse(ObjC.unwrap(raw));
 if(Number(doc.pageCount)!==manifest.pageCount)throw Error('Wrong PDF page count');
 const normalize=s=>s.normalize('NFKC').replace(/\s+/g,' ').trim();
 const text=normalize(ObjC.unwrap(doc.string)||'');for(const item of manifest.requiredSelectableText)if(!text.includes(normalize(item)))throw Error('Missing selectable caption');
 return JSON.stringify({pageCount:Number(doc.pageCount),selectableTextVerified:true,verifier:'system PDFKit/JXA',extractedCharacters:text.length});
}
