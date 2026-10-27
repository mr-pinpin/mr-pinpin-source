#!/usr/bin/env python3
"""Build native ARM application and package using the existing PlxNative mkipk tool."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

APP_ID = 'com.mrpinpin.family'
VERSION = '0.1.0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True, help='Verified prepare_assets.py output')
    parser.add_argument('--packager', type=Path, required=True, help='Existing PlxNative ci/mkipk.py')
    parser.add_argument('--output', type=Path, required=True, help='External build directory')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    args.output = args.output.resolve()
    data = args.output / 'data'
    app = data / 'usr/palm/applications' / APP_ID
    app.mkdir(parents=True, exist_ok=True)
    # Require exact verified exports; do not package arbitrary asset directories.
    import hashlib
    provenance = json.loads((args.assets / 'provenance.json').read_text())
    spec = json.loads((here / 'inputs.json').read_text())
    entries = provenance['inputs']
    if len(entries) != len(spec['assets']):
        raise SystemExit('Incomplete prepared assets')
    (app / 'assets').mkdir(exist_ok=True)
    for expected, record in zip(spec['assets'], entries):
        if any(record.get(key) != expected[key] for key in ('source','output','sha256','size')):
            raise SystemExit('Prepared asset provenance differs from pinned input manifest')
        payload = (args.assets / expected['output']).read_bytes()
        if len(payload) != expected['size'][0]*expected['size'][1]*4 or hashlib.sha256(payload).hexdigest() != record['derivativeSha256']:
            raise SystemExit('Prepared asset checksum or dimensions mismatch')
        (app / 'assets' / expected['output']).write_bytes(payload)
    shutil.copy2(args.assets / 'provenance.json', app / 'assets/provenance.json')
    compiler = args.sdk / 'bin/arm-webos-linux-gnueabi-gcc'
    sysroot = args.sdk / 'arm-webos-linux-gnueabi/sysroot'
    command = [str(compiler),f'--sysroot={sysroot}','-std=c11','-D_GNU_SOURCE','-O2','-Wall','-Wextra','-Werror',
               '-mcpu=cortex-a9','-mfloat-abi=softfp', '-fno-omit-frame-pointer','-Wl,--build-id=sha1',
               f'-ffile-prefix-map={root}=/family-source', str(here/'main.c'),'-o',str(app/'family-native'),
               '-lSDL2','-lGLESv2','-lm']
    subprocess.run(command, check=True)
    appinfo = {'id':APP_ID,'version':VERSION,'type':'native','main':'family-native','title':'MrPomPom',
               'appDescription':'Native family Atlas pilot','vendor':'Mr. PinPin','icon':'icon.png','largeIcon':'largeIcon.png',
               'mediumLargeIcon':'mediumLargeIcon.png','extraLargeIcon':'extraLargeIcon.png','iconColor':'#314902',
               'resolution':'1920x1080','handlesRelaunch':False}
    for name, size in [('icon.png',80),('largeIcon.png',130),('mediumLargeIcon.png',160),('extraLargeIcon.png',320)]:
        shutil.copy2(here/f'icon/mrpompom-family-icon-{size}-v1.png', app/name)
    (app/'appinfo.json').write_text(json.dumps(appinfo,indent=2)+'\n')
    for name in ('LICENSE','LICENSE-MIT','CONTENT-LICENSE.md','THIRD-PARTY-NOTICES.md'):
        shutil.copy2(root/name,app/name)
    shutil.copy2(here/'README.md',app/'NATIVE-README.md')
    shutil.copy2(here/'icon/README.md',app/'ICON-LICENSE.md')
    shutil.copy2(here/'icon/provenance.json',app/'icon-provenance.json')
    # Existing GPL build tool is used unmodified, not copied into MIT application code.
    sys.path.insert(0,str(args.packager.resolve().parent))
    module_spec=importlib.util.spec_from_file_location('family_existing_mkipk',args.packager)
    packager=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(packager)
    # The shared tool's write_packageinfo assumes its own separate storage service.
    # This app has none: emit only the native app's standard package descriptor.
    package_dir=data/'usr/palm/packages'/APP_ID
    package_dir.mkdir(parents=True,exist_ok=True)
    (package_dir/'packageinfo.json').write_text(json.dumps({'app':APP_ID,'id':APP_ID,'loc_name':'MrPomPom','version':VERSION,'vendor':'Mr. PinPin','package_format_version':2},indent=2)+'\n')
    control=args.output/'control';control.mkdir(exist_ok=True)
    installed=(sum(p.stat().st_size for p in data.rglob('*') if p.is_file())+1023)//1024
    (control/'control').write_text(f'Package: {APP_ID}\nVersion: {VERSION}\nSection: misc\nPriority: optional\nArchitecture: arm\nInstalled-Size: {installed}\nMaintainer: Mr. PinPin\nDescription: Native family Atlas pilot\nwebOS-Package-Format-Version: 2\nwebOS-Packager-Version: family-native/shared-mkipk\n')
    archive=args.output/f'{APP_ID}_{VERSION}_arm.ipk'
    packager.write_targz(args.output/'control.tar.gz',control,'.')
    packager.write_targz(args.output/'data.tar.gz',data,'.')
    packager.write_ar(archive,[('debian-binary',b'2.0\n'),('control.tar.gz',(args.output/'control.tar.gz').read_bytes()),('data.tar.gz',(args.output/'data.tar.gz').read_bytes())])
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (args.output/'package.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'{archive}\nsha256 {digest}')


if __name__ == '__main__':
    main()
