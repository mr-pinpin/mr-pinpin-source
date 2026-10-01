#!/usr/bin/env python3
"""Copy selected illustration panels into reproducible captioned comic boards."""
import argparse, hashlib, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, __version__ as pillow_version

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def wrap(text, font, width, draw):
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            if draw.textlength(word, font=font) > width:
                raise ValueError("Word too wide for caption cell: " + word)
            candidate = (line + " " + word).strip()
            if line and draw.textlength(candidate, font=font) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines

def localized(value, language):
    return value.get(language, value.get("en", "")) if isinstance(value, dict) else value

def build(args):
    pack = args.pack.resolve()
    layout_path = (args.layout or pack / "storyboard-layout.json").resolve()
    plan_path = (args.plan or pack / "story-plan.json").resolve()
    cfg = json.loads(layout_path.read_text())
    source = Path(args.source_pack or cfg["sourcePack"]).resolve()
    media_path = source / "media.json"
    media = json.loads(media_path.read_text())
    plan_bytes=plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    plan_sha=hashlib.sha256(plan_bytes).hexdigest()
    scenes = {s["id"]: s for s in plan["scenes"]}
    used = [panel["scene"] for group in cfg["groups"] for panel in group["panels"] if panel["scene"]]
    if len(used) != len(set(used)):
        raise ValueError("Duplicate scene in storyboard layout")
    if cfg.get("requireEveryScene", True) and set(used) != set(scenes):
        raise ValueError("Storyboard layout does not cover exactly the plan scenes")
    if not args.allow_pending and any(scene not in media["images"] for scene in used):
        raise ValueError("Unillustrated scene: use --allow-pending only for explicit preproduction")
    width, columns = cfg["width"], cfg["columns"]
    margin, gap = cfg["margin"], cfg["gap"]
    cell = (width - 2 * margin - (columns - 1) * gap) // columns
    image_height = round(cell * 2 / 3)
    font_path = Path(cfg["fontPath"])
    font = ImageFont.truetype(str(font_path), cfg["captionFontSize"])
    header_font = ImageFont.truetype(str(font_path), 48)
    label_font = ImageFont.truetype(str(font_path), 29)
    beat_font = ImageFont.truetype(str(font_path), 23)
    line_height = sum(font.getmetrics()) + 6
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    outputs = []
    input_cache = {}
    for language in args.languages.split(","):
        for number, group in enumerate(cfg["groups"], 1):
            panels = []
            for spec in group["panels"]:
                scene_id = spec["scene"]
                if scene_id:
                    scene = scenes[scene_id]
                    paragraphs = scene["paragraphs"].get(language)
                    if not paragraphs:
                        raise ValueError("Missing caption " + language + " " + scene_id)
                    caption = "\n".join(paragraphs)
                    label = str(scene["number"]).zfill(2)+" · "+str(scene.get("feedbackLabel") or ("R9 "+str(scene.get("sourceSceneNumber",scene["id"].replace("scene-","")))))
                    selected = media["images"].get(scene_id)
                    if selected:
                        origin=pack.parent/("pinpin-"+selected.get("sourceProduction",pack.name.removeprefix("pinpin-")))
                        path=origin/selected["path"]
                        if str(path) not in input_cache:
                            digest=sha(path)
                            if digest!=selected["sha256"]:raise ValueError("Selected illustration hash mismatch: "+scene_id)
                            input_cache[str(path)]=digest
                        panel_input={"path":str(path),"sha256":input_cache[str(path)]}
                    else:panel_input=None
                else:
                    caption = localized(spec.get("instruction", ""), language)
                    label = localized(spec.get("label", {"en":"Future panel","ru":"Будущий кадр"}), language)
                    panel_input = None
                beat = scenes[scene_id].get("readingBeat", {}) if scene_id else {}
                kind = beat.get("kind", "")
                beat_label = localized(plan.get("readingBeatLegend", {}).get(kind, kind), language) if cfg.get("showReadingBeat",False) else ""
                lines = wrap(caption, font, cell - 24, probe)
                panels.append({"sceneId":scene_id,"caption":caption,"label":label,
                               "lines":lines,"input":panel_input,"readingBeat":beat,"readingBeatLabel":beat_label})
            rows = [panels[i:i+columns] for i in range(0,len(panels),columns)]
            row_heights = [image_height + 55 + max(len(p["lines"]) for p in row)*line_height + 22 for row in rows]
            header_height = 122
            height = margin + header_height + sum(row_heights) + gap*(len(rows)-1) + margin
            canvas = Image.new("RGB", (width,height), "#fcf7eb")
            draw = ImageDraw.Draw(canvas)
            title = f'{number}/{len(cfg["groups"])} · {localized(group["title"],language)}'
            draw.text((margin,margin), title, font=header_font, fill="#443424")
            subtitle = "Мистер ПинПин · раскадровка" if language=="ru" else "Mr. PinPin · chapter storyboard"
            draw.text((margin,margin+65), subtitle, font=label_font, fill="#746652")
            y = margin + header_height
            for row, row_height in zip(rows,row_heights):
                for column, panel in enumerate(row):
                    x = margin + column*(cell+gap)
                    draw.rectangle((x,y,x+cell,y+row_height), fill="#fffdf8")
                    if panel["input"]:
                        with Image.open(panel["input"]["path"]) as original:
                            tile = ImageOps.contain(original.convert("RGB"), (cell,image_height), Image.Resampling.LANCZOS)
                            canvas.paste(tile,(x+(cell-tile.width)//2,y+(image_height-tile.height)//2))
                    else:
                        draw.rectangle((x+1,y+1,x+cell-1,y+image_height-1), outline="#b7aa95",width=3)
                        pending="Новая иллюстрация — в работе" if language=="ru" else "New illustration — pending"
                        draw.text((x+20,y+25),pending,font=label_font,fill="#746652")
                        draw.text((x+20,y+75),panel["label"],font=label_font,fill="#746652")
                    draw.text((x+12,y+image_height+8),panel["label"],font=label_font,fill="#6e502f")
                    if panel["readingBeatLabel"]:
                        pill = panel["readingBeatLabel"]
                        pill_width = draw.textlength(pill,font=beat_font) + 22
                        if pill_width > cell - 90:
                            raise ValueError("Reading-beat pill too wide")
                        draw.rounded_rectangle((x+78,y+image_height+7,x+78+pill_width,y+image_height+39),radius=12,fill="#e9dfc9")
                        draw.text((x+89,y+image_height+10),pill,font=beat_font,fill="#685537")
                    for line_index,line in enumerate(panel["lines"]):
                        draw.text((x+12,y+image_height+50+line_index*line_height),line,font=font,fill="#2d261f")
                    panel.update({"x":x,"y":y,"width":cell,"height":row_height})
                    del panel["lines"]
                y += row_height + gap
            slug=f"storyboard-{number:02}-{language}"
            web = pack/"boards"/(slug+".webp")
            master = pack/"boards"/"masters"/(slug+f"-v{args.version}.png")
            web.parent.mkdir(parents=True,exist_ok=True)
            master.parent.mkdir(parents=True,exist_ok=True)
            canvas.save(master,compress_level=6)
            canvas.save(web,"WEBP",quality=cfg["webpQuality"],method=6)
            ids = [p["sceneId"] for p in panels if p["sceneId"]]
            outputs.append({"language":language,"number":number,
                            "path":str(web.relative_to(pack)),"sha256":sha(web),"bytes":web.stat().st_size,
                            "master":str(master.relative_to(pack)),"masterSha256":sha(master),
                            "width":width,"height":height,
                            "sceneStart":scenes[ids[0]]["number"] if ids else None,
                            "sceneEnd":scenes[ids[-1]]["number"] if ids else None,
                            "pendingPanels":sum(panel["input"] is None for panel in panels),
                            "panels":panels})
            print(json.dumps({"path":str(web),"dimensions":[width,height],"bytes":web.stat().st_size}),flush=True)
    manifest={"schemaVersion":1,"operation":"layout-only: contain, copy, caption; no generated or retouched artwork",
              "sourcePack":str(source),"plan":{"path":str(plan_path),"sha256":plan_sha},
              "layout":{"path":str(layout_path),"sha256":sha(layout_path)},
              "tool":{"path":str(Path(__file__).resolve()),"sha256":sha(__file__),"pillow":pillow_version},
              "font":{"path":str(font_path),"sha256":sha(font_path)},
              "boards":outputs,"pendingPanels":sum(b["pendingPanels"] for b in outputs),"version":args.version,"preproduction":args.allow_pending}
    (pack/"boards"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--plan",type=Path)
    parser.add_argument("--layout",type=Path)
    parser.add_argument("--source-pack",type=Path)
    parser.add_argument("--languages",default="ru,en")
    parser.add_argument("--allow-pending",action="store_true")
    parser.add_argument("--version",type=int,default=1)
    build(parser.parse_args())
