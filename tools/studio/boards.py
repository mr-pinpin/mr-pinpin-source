"""Immutable contact sheets from actual selected images and caption snapshots."""
import copy
import io
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
from model import StudioError, LANGUAGES, caption, find, new_id, now
from store import atomic_json, digest


def font(size, bold=False):
    choices = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
               "/System/Library/Fonts/Supplemental/Arial.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def wrap(text, face, width):
    lines = []
    for paragraph in text.splitlines() or [""]:
        line = ""
        for word in paragraph.split():
            if line and face.getlength(line + " " + word) > width:
                lines.append(line)
                line = ""
            while face.getlength(word) > width:
                cut = max(1, int(len(word) * width / max(1, face.getlength(word))))
                while cut > 1 and face.getlength(word[:cut]) > width:
                    cut -= 1
                if line:
                    lines.append(line)
                    line = ""
                lines.append(word[:cut])
                word = word[cut:]
            line = (line + " " + word).strip()
        lines.append(line)
    return lines


def create_storyboard(store, request):
    count = request.get("panelsPerPage", 12)
    language = request.get("language", "en")
    if count not in (6, 12, 24) or language not in LANGUAGES:
        raise StudioError("Choose 6,12,24 panels and en,ru,es")
    snapshot = store.read()
    chapter = copy.deepcopy(find(snapshot["project"]["chapters"], request.get("chapterId"), "chapter"))
    if not chapter.get("scenes"):
        raise StudioError("Add scenes before making a storyboard")
    asset_map = {a["id"]: a for a in snapshot["assets"]}
    image_hashes = {s["imageAssetId"]: asset_map[s["imageAssetId"]]["sha256"]
                    for s in chapter["scenes"] if s.get("imageAssetId")}
    frozen = {"chapter": chapter, "imageHashes": image_hashes,
              "language": language, "panelsPerPage": count, "projectRevision": snapshot["revision"]}
    board = {"id": new_id("board"), "chapterId": chapter["id"], "language": language,
             "panelsPerPage": count, "createdAt": now(), "projectRevision": snapshot["revision"],
             "snapshotSha256": digest(json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode()),
             "pages": []}
    snapshot_path = store.root / "storyboards" / board["id"] / "snapshot.json"
    atomic_json(snapshot_path, frozen)
    board["snapshotPath"] = str(snapshot_path)
    generated = []
    cols = 4 if count == 24 else 3
    rows = count // cols
    tile_width, gutter, margin, header_height = 480 if cols == 3 else 360, 16, 24, 86
    image_height = int(tile_width * 2 / 3)
    tile_height = image_height + 154
    width = margin * 2 + cols * tile_width + (cols - 1) * gutter
    height = header_height + margin + rows * tile_height + (rows - 1) * gutter
    title_face, body_face, small_face = font(28, True), font(18), font(17, True)
    title_value = chapter.get("title", {})
    title = title_value.get(language, chapter["id"]) if isinstance(title_value, dict) else str(title_value)
    for offset in range(0, len(chapter["scenes"]), count):
        im = Image.new("RGB", (width, height), "#efe7d6")
        draw = ImageDraw.Draw(im)
        page_number = offset // count + 1
        draw.text((margin, 20), title[:85] + "  ·  " + language.upper(), font=title_face, fill="#372c24")
        draw.text((margin, 56), "Storyboard · " + str(page_number), font=small_face, fill="#735d47")
        panels = []
        for index, scene in enumerate(chapter["scenes"][offset:offset + count]):
            x = margin + (index % cols) * (tile_width + gutter)
            y = header_height + (index // cols) * (tile_height + gutter)
            draw.rounded_rectangle((x, y, x + tile_width, y + tile_height), radius=8, fill="#fffaf0")
            asset_id = scene.get("imageAssetId")
            if asset_id:
                with Image.open(store.asset_path(asset_id, snapshot)) as source:
                    picture = ImageOps.contain(source.convert("RGB"), (tile_width, image_height))
                    im.paste(picture, (x + (tile_width - picture.width) // 2, y + (image_height - picture.height) // 2))
            else:
                draw.rectangle((x + 10, y + 10, x + tile_width - 10, y + image_height - 10),
                               fill="#e4dbca", outline="#bcaa8b", width=2)
                draw.text((x + 24, y + image_height // 2 - 12), "Awaiting artwork", font=body_face, fill="#766653")
            label = str(offset + index + 1) + " · " + scene["id"]
            draw.text((x + 12, y + image_height + 9), label, font=small_face, fill="#514331")
            text = caption(scene, language)
            lines = wrap(text, body_face, tile_width - 24)
            if len(lines) > 5:
                lines = lines[:5]
                lines[-1] = lines[-1].rstrip(" .") + "…"
            for line_no, line in enumerate(lines):
                draw.text((x + 12, y + image_height + 36 + line_no * 21), line, font=body_face, fill="#342c24")
            panels.append({"sceneId": scene["id"], "index": offset + index,
                           "caption": text, "imageAssetId": asset_id,
                           "imageSha256": image_hashes.get(asset_id),
                           "box": [x, y, tile_width, tile_height]})
        buffer = io.BytesIO()
        im.save(buffer, "PNG")
        asset = store.prepare_asset(buffer.getvalue(), board["id"] + "-page-" + str(page_number) + ".png",
                                    {"kind": "storyboard-sheet", "storyboardId": board["id"],
                                     "snapshotSha256": board["snapshotSha256"]})
        generated.append(asset)
        board["pages"].append({"id": new_id("page"), "assetId": asset["id"], "url": asset["url"],
                               "index": page_number - 1, "panels": panels,
                               "reviewStatus": "unreviewed", "feedback": []})

    def register(state):
        for asset in generated:
            store.register_asset(state, asset)
        state["storyboards"].append(board)
        store.event(state, "storyboard.created", storyboardId=board["id"], chapterId=chapter["id"])
        return board
    return store.mutate(register)


def review_storyboard(store, identifier, request):
    decision = request.get("decision")
    if decision not in ("feedback", "approve", "reject"):
        raise StudioError("Unknown review decision")
    def review(state):
        board = find(state["storyboards"], identifier, "storyboard")
        page = find(board["pages"], request.get("pageId"), "page")
        scene_id = request.get("sceneId")
        if scene_id and scene_id not in {p["sceneId"] for p in page["panels"]}:
            raise StudioError("Scene is not on this page")
        feedback = {"id": new_id("feedback"), "author": "user", "decision": decision,
                    "text": str(request.get("feedback", "")), "sceneId": scene_id,
                    "createdAt": now(), "resolved": decision != "feedback"}
        page["feedback"].append(feedback)
        if decision != "feedback":
            status = "user-approved" if decision == "approve" else "user-rejected"
            if scene_id:
                next(p for p in page["panels"] if p["sceneId"] == scene_id)["reviewStatus"] = status
            else:
                page["reviewStatus"] = status
        store.event(state, "storyboard.reviewed", storyboardId=identifier, pageId=page["id"],
                    sceneId=scene_id, feedbackId=feedback["id"], decision=decision)
        return board
    return store.mutate(review)
