"""Save named studio files and synchronize the current workspace."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


class SyncError(Exception):
    pass


def git(*arguments, allowed=(0,), network=False):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    result = subprocess.run(
        ["git", "--literal-pathspecs", *arguments],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30 if network else None,
    )
    if result.returncode not in allowed:
        raise SyncError(result.stderr.strip() or result.stdout.strip() or "Git failed.")
    return result


def output(*arguments):
    return git(*arguments).stdout.strip()


def upstream():
    branch = output("symbolic-ref", "HEAD")
    tracking = output(
        "for-each-ref",
        "--format=%(upstream:remotename)%09%(upstream:remoteref)",
        branch,
    ).split("\t")
    if len(tracking) != 2 or tracking[0] in ("", ".") or not tracking[1].startswith("refs/heads/"):
        raise SyncError("The current branch has no shared destination.")
    return tracking


def fetch(remote):
    git("fetch", "--quiet", "--no-tags", "--", remote, network=True)
    return output("rev-parse", "--verify", "@{upstream}")


def contains(ancestor, revision):
    return git("merge-base", "--is-ancestor", ancestor, revision, allowed=(0, 1)).returncode == 0


def refresh():
    remote, _ = upstream()
    latest = fetch(remote)
    if not contains(latest, "HEAD"):
        git("merge", "--ff-only", "--no-autostash", "--no-overwrite-ignore", latest)


def save(message, paths):
    parent = output("rev-parse", "HEAD")
    listed = git(
        "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", *paths
    ).stdout.split("\0")
    if any(path not in listed for path in paths):
        raise SyncError("Name individual tracked or unignored files using workspace-relative paths.")
    git("add", "--intent-to-add", "-A", "--", *paths)
    if git("diff", "--quiet", "HEAD", "--", *paths, allowed=(0, 1)).returncode == 0:
        return
    git("commit", "--quiet", "--only", "--message", message, "--", *paths)
    revision = output("rev-parse", "HEAD")
    changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", revision).stdout
    if output("rev-list", "--parents", "-n", "1", revision).split() != [revision, parent] or (
        set(changed.rstrip("\0").split("\0")) - set(paths)
    ):
        raise SyncError("Check the saved version before sharing. The branch or file list changed.")
    print(revision)


def share(revision):
    remote, destination = upstream()
    if output("remote", "get-url", "--push", "--all", remote) != output(
        "remote", "get-url", remote
    ):
        raise SyncError("The upload destination differs from the download source.")
    revision = output("rev-parse", "--verify", "--end-of-options", revision + "^{commit}")
    if not contains(revision, "HEAD"):
        raise SyncError("Select a saved version from the current branch.")
    latest = fetch(remote)
    if contains(revision, latest):
        return
    if output("rev-list", "--parents", "-n", "1", revision).split() != [revision, latest]:
        raise SyncError("The shared copy and this saved version need to be reconciled first.")
    git(
        "-c", f"remote.{remote}.mirror=false",
        "push", "--quiet", "--no-follow-tags", "--recurse-submodules=no", "--",
        remote, f"{revision}:{destination}", network=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("refresh", help="Get the latest available shared work")
    save_parser = commands.add_parser("save", help="Save only the named files here")
    save_parser.add_argument("-m", "--message", required=True)
    save_parser.add_argument("paths", nargs="+")
    share_parser = commands.add_parser("share", help="Share one authorized saved version")
    share_parser.add_argument("revision")
    args = parser.parse_args()
    try:
        if args.command == "refresh":
            refresh()
        elif args.command == "save":
            save(args.message, args.paths)
        else:
            share(args.revision)
    except (SyncError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Studio sync: {exc}", file=sys.stderr)
        return 1
    return 0


ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    sys.exit(main())
