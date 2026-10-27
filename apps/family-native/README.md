# Native family Atlas pilot

This separate `com.mrpinpin.family` application renders the existing illustrated
Atlas through SDL2 and GLES2. It contains no HTML, browser or WebView. The first
milestone has pointer/OK destinations, D-pad cursor fallback, camera easing and
Mr. PinPin's existing eight-direction walking animation. It does not yet include
the book reader, family-following animation, pathfinding or the website's layered
terrain. Clicking traverses the illustration directly; it is not a claim that all
visible ground is walkable. Back exits, and background focus pauses rendering.

This is a private family pilot, not an official reader release. Original story,
illustration and sprite files are neither edited nor relicensed. `inputs.json`
pins existing asset SHA256 values. `prepare_assets.py` checks every original and
exports only lossless RGBA pixel data into an external build directory. The map,
artwork and creative configuration retain the root CONTENT-LICENSE.md boundary;
new functional C/Python software is covered by the root MIT software grant.
Generated app icon has its own provenance under `icon/`. No GPL application code
was copied: native-platform setup was checked against the working PlxNative app;
the existing GPL-3.0-or-later PlxNative `ci/mkipk.py` is invoked unmodified as a
separate build tool. The icon's specific redistribution notice is included in the package separately.
SDL2 is system-provided under its upstream zlib license and
GLES2 is the TV's platform API. No third-party shared libraries are bundled.

## Build

Use the existing warm webOS NDK. Pillow is required only for verified asset export.
Restore missing walk sheets through the repository's verified asset workflow, or
point `--asset-root` to an existing restored checkout. No creative regeneration is
needed. Never write build output into canonical assets.

```sh
python3 apps/family-native/prepare_assets.py --asset-root /path/to/restored-source --output /external/family/assets
python3 apps/family-native/build.py --sdk /path/to/webos-ndk/arm-webos-linux-gnueabi_sdk-buildroot --assets /external/family/assets --packager /path/to/plx-native/ci/mkipk.py --output /external/family/build
```

The resulting `.ipk` contains a native ELF, package descriptor, icon variants,
existing art exports with provenance and licensing notices. Install using the
existing TV transport and native-device operation lock. Verify ELF dependencies,
package SHA256 and the installed version before claiming a successful deployment.
Do not replace the factory launcher or another application. Real pointer input,
background lifecycle and frame pacing require the actual TV; host syntax checks
are not device evidence. Render counters are diagnostics, not a measured FPS claim.
