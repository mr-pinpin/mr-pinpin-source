# Cupola lake: reproducible authored blocking

Read `../CANON-AND-CUPOLA.md` for the actual original-book connections and the
author's confirmed design. Geometry guides and original-book style images have
different roles. This is a new proposed location, not recovered book measurements.

The location pins its plan, builder and original image inputs. Use the existing
renderer, with the heavy output outside the checkout:

```sh
python3 tools/locations/cli.py build --location docs/storyboard/production/scooby-cave-r7-20261013/geometry/location.json --out NEW_EXTERNAL_BUILD --blender BLENDER
python3 tools/locations/cli.py render --job docs/storyboard/production/scooby-cave-r7-20261013/geometry/lake-reveal.json --build EXTERNAL_BUILD --out NEW_EXTERNAL_REVEAL --blender BLENDER
python3 tools/locations/cli.py cubemap --job docs/storyboard/production/scooby-cave-r7-20261013/geometry/lake-cubemap.json --build EXTERNAL_BUILD --out NEW_EXTERNAL_CUBE --blender BLENDER
python3 tools/locations/cli.py prepare --job docs/storyboard/production/scooby-cave-r7-20261013/geometry/lake-reveal.json --from-manifest EXTERNAL_REVEAL/render-manifest.json --out NEW_EXTERNAL_PREPARED
```

Before-screen and shore-reverse are separately recorded origins. Turning the
lake cube uses its one origin; it does not move the camera along the shore.
The renderer's optional `structuralObject` names the new cave shell, retaining
the default house object name for the unchanged house workflow. Mesh and
source/artifact checks are separate from illustration quality.

Plant boxes are blocking markers to replace with growing vegetation in an
illustration; no crates, columns, torches or extra skylights are implied. A
generated cubemap is one whole-atlas image call followed by real viewer/join
inspection. Keep the source render, exact prompt, original output and selected
derivatives separately. Do not make independent six-face illustrations.
