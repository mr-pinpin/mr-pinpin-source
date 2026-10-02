#!/usr/bin/env python3
import argparse,pathlib,json,hashlib,shutil,datetime
from PIL import Image
P=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
a=argparse.ArgumentParser();a.add_argument("id");a.add_argument("source");a.add_argument("--version",default="v1");a.add_argument("--pass-root",action="store_true");a=a.parse_args()
source=pathlib.Path(a.source);master=P/"masters"/f"{a.id}-{a.version}.png"
if source!=master:shutil.copyfile(source,master)
assert sha(source)==sha(master)
args=json.loads((P/"records"/f"{a.id}-{a.version}-arguments.json").read_text())
prompt=P/"prompts"/f"{a.id}-{a.version}.txt";prompt.write_text(args["prompt"])
web=P/"web"/f"{a.id}-{a.version}.webp"
with Image.open(master) as im:im.convert("RGB").save(web,"WEBP",quality=92,method=6);size=list(im.size)
rec={"id":a.id,"version":a.version,"tool":"image_gen__imagegen","toolArguments":args,"master":str(master),"native":str(master),"sha256":sha(master),"nativeSha256":sha(master),"web":str(web),"webSha256":sha(web),"dimensions":size,"originalToolOutput":str(source),"originalToolSha256":sha(source),"prompt":str(prompt),"promptSha256":sha(prompt),"references":[{"path":x,"sha256":sha(x)} for x in args["referenced_image_paths"]],"rootReview":"pass" if a.pass_root else "pending","userReview":"pending","createdAt":datetime.datetime.now(datetime.timezone.utc).isoformat()}
record=P/"records"/f"{a.id}-{a.version}.json";rec["record"]=str(record);record.write_text(json.dumps(rec,indent=2)+"\n")
if a.pass_root:
 s=P/"selection.json";d=json.loads(s.read_text()) if s.exists() else {"selected":{}};d["selected"][a.id]=rec;s.write_text(json.dumps(d,indent=2)+"\n")
print(json.dumps({"id":a.id,"native":str(master),"record":str(record),"rootReview":rec["rootReview"]}))

