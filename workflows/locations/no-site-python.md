# Prepared no-site Python helper

Native same-thread acceptance showed normal Python starts blocked before entry; -S preserved sandbox/security and completed reads. Install exact source tools/studio-client/studio-python as DATA/tools/studio-python with executable owner mode. This wrapper executes configured Python with -S -B and explicit dependencies/PYTHONPATH; no .pth or sitecustomize startup.

Set PINPIN_STUDIO_DATA, PINPIN_STUDIO_RUNTIME, PINPIN_STUDIO_SOURCE and optional PINPIN_STUDIO_DEPENDENCIES (default DATA sibling dependencies), PINPIN_STUDIO_PYTHON (default /opt/homebrew/bin/python3) in trusted host environment. Source wrapper is an installation artifact; DATA/tools is its intended default installed location. Never read roots from request/project JSON.

Preserve four-entry workflows/toolchain.json argvPrefix: [DATA/tools/studio-python, SOURCE/tools/studio-client/register-image.py, --runtime-dir, RUNTIME]. Keep actual helperSha256 verified. Include pythonStartupFlags [-S,-B] and pythonDependencies path. Prefix cast/storage commands with exact installed wrapper; helper nested sys.executable subprocesses must explicitly add -S -B. Storage policy pythonPath may use wrapper once HF SDK dependency closure is explicitly configured/verified; PIL dependency cache alone covers registration/chapter context, not HF transfer. Never infer remote proof from local readiness.

Chapter context hints use python -S -B tools/chapter_draft_ops.py; inherited PYTHONPATH must include exact cached same-ABI Pillow. Tests use disposable data/runtime copies. Stable kernel and sandbox enforcement remain unchanged.
