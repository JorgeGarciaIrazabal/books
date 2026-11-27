# Workspace sync for studio operators

The author can ask to continue or save progress in ordinary language. The studio
director runs the following from the workspace root using the available Python 3
command (`python`, `python3`, or `py -3`). Reviewers and other specialists return
their work to the director so that one session owns synchronization.

1. At the start or resumption of an assignment, run
   `python tools/studio_sync.py refresh`. Repeat before starting another
   substantial stage and when preparing the handoff. This fetches the current
   branch's upstream and advances the local copy when Git can do so safely.
2. After a coherent milestone such as a chapter revision, editorial pass,
   approved asset selection, or final handoff, save the exact files owned by
   the current task. For example,
   `python tools/studio_sync.py save -m "Revise chapter three" path/to/chapter.md`.
   Inspect those files first, especially if a selected file also contains
   pre-existing user edits. Use individual workspace-relative paths with forward
   slashes. The command prints the new saved version if there is a change.
3. When the saved version is eligible for the configured destination, run
   `python tools/studio_sync.py share <saved-version>` immediately after saving.
   Use the printed version and the same working copy. This checks for newer
   shared work before uploading and only sends the named version when its parent
   is the current shared tip. For several pending authorized saves, send them
   in order. A retry of an already-shared version succeeds quietly.

These steps run during active studio sessions, including after meaningful
milestones in a long session. Keep successful sync out of routine updates.
Each computer needs a checkout of the same authorized workspace with access
and a tracking branch. When switching computers, the next session refreshes
before using its local handoff.

## Where saved work can go

- The current `origin` repository is public. Share studio maintenance covered
  by the user's sync request and versions already authorized for public release.
  Keep unpublished drafts, private editorial notes, voice samples, credentials,
  and unrelated edits off that destination, including other branches.
- For a verified private workspace already authorized by the author for drafts,
  use its tracking branch and share in-scope progress automatically. Verify
  the destination before the first upload and whenever it changes. Keep
  publication decisions separate from private saving.
- Save locally when offline, when a draft has no authorized private destination,
  or when the remote moved. Reconcile compatible changes before sharing.
  Preserve both versions if edits overlap and need the author's judgment.
  Leave unrelated work and existing staged changes in place. The helper never
  force-pushes, stashes edits, or decides how to combine conflicting drafts.
- Locally generated exports and listening files under ignored directories do
  not travel with source saves. Share a preview using the authorized delivery
  method for that artifact. A request for a preview leaves public release up
  to the author.
