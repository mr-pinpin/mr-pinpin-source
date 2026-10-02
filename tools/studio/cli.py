#!/usr/bin/env python3
"""Agent CLI: claim real work, preserve actual outputs, and reply to feedback."""
import argparse
import json
import sys
from pathlib import Path
from model import StudioError
from store import Store, atomic_json
from jobs import claim_job, complete_job, fail_job, reply, inbox


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--media-root", action="append", default=[])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("jobs")
    sub.add_parser("inbox")
    sub.add_parser("history")
    command = sub.add_parser("export-project")
    command.add_argument("--output", required=True)
    command.add_argument("--revision", type=int)
    command = sub.add_parser("import-asset")
    command.add_argument("path")
    command.add_argument("--name")
    command.add_argument("--review-status", default="unreviewed")
    for name in ("claim", "complete", "fail", "reply"):
        command = sub.add_parser(name)
        command.add_argument("id")
        command.add_argument("--agent", required=True)
        if name == "complete":
            output = command.add_mutually_exclusive_group(required=True)
            output.add_argument("--image")
            output.add_argument("--text-file")
            command.add_argument("--scene-id")
            command.add_argument("--visual-pass", action="store_true")
            command.add_argument("--tool")
            prompt = command.add_mutually_exclusive_group()
            prompt.add_argument("--prompt-file")
            prompt.add_argument("--used-job-prompt", action="store_true")
            references = command.add_mutually_exclusive_group()
            references.add_argument("--references-file")
            references.add_argument("--used-job-references", action="store_true")
        elif name == "fail":
            command.add_argument("--reason", required=True)
        elif name == "reply":
            command.add_argument("--text", required=True)
            command.add_argument("--feedback-id")
    args = parser.parse_args(argv)
    store = Store(args.data_dir, args.media_root)
    try:
        if args.command == "jobs":
            result = {"jobs": store.read()["jobs"]}
        elif args.command == "inbox":
            result = inbox(store)
        elif args.command == "history":
            result = {"revisions": store.project_history()}
        elif args.command == "export-project":
            result = store.project_revision(args.revision)["project"] if args.revision is not None else store.read()["project"]
            atomic_json(Path(args.output).expanduser(), result)
            result = {"output": str(Path(args.output).resolve())}
        elif args.command == "import-asset":
            result = {"asset": store.import_asset(args.path, args.name, review_status=args.review_status)}
        elif args.command == "claim":
            result = {"job": claim_job(store, args.id, args.agent)[0]}
        elif args.command == "fail":
            result = {"job": fail_job(store, args.id, args.agent, args.reason)[0]}
        elif args.command == "reply":
            result = {"target": reply(store, args.id, args.agent, args.text, args.feedback_id)[0]}
        else:
            text = Path(args.text_file).read_text() if args.text_file else None
            prompt = Path(args.prompt_file).read_text() if args.prompt_file else None
            references = json.loads(Path(args.references_file).read_text()) if args.references_file else None
            result = {"job": complete_job(store, args.id, args.agent, args.image, text, args.scene_id,
                prompt, references, args.used_job_prompt, args.used_job_references, args.tool, args.visual_pass)[0]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (StudioError, OSError, ValueError) as exc:
        error = exc.payload() if isinstance(exc, StudioError) else {"error": {"code": "cli_input", "message": str(exc)}}
        print(json.dumps(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
