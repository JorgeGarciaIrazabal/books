#!/usr/bin/env bash
set -euo pipefail

BUMP="${BUMP:-patch}"
REMOTE="${REMOTE:-origin}"
DRY_RUN="${DRY_RUN:-0}"
SKIP_CHECKS="${SKIP_CHECKS:-0}"

case "${BUMP}" in
  patch|minor|major) ;;
  *)
    echo "Error: BUMP must be 'patch', 'minor', or 'major' (got '${BUMP}')." >&2
    exit 1
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel)"
DESKTOP_DIR="${REPO_ROOT}/studio-desktop"
PKG_JSON="${DESKTOP_DIR}/package.json"

if [ ! -f "${PKG_JSON}" ]; then
  echo "Error: Could not find ${PKG_JSON}" >&2
  exit 1
fi

BRANCH="$(git -C "${REPO_ROOT}" symbolic-ref --quiet --short HEAD || true)"
if [ -z "${BRANCH}" ]; then
  if [ "${DRY_RUN}" = "1" ]; then
    echo "Warning: Detached HEAD detected (dry run continues)." >&2
    BRANCH="<detached-head>"
  else
    echo "Error: Repository is in detached HEAD state. Check out a branch before cutting a release." >&2
    exit 1
  fi
fi

DIRTY_FILES="$(git -C "${REPO_ROOT}" status --porcelain)"
if [ -n "${DIRTY_FILES}" ]; then
  if [ "${DRY_RUN}" = "1" ]; then
    echo "Warning: Working tree has uncommitted changes (dry run continues)." >&2
  else
    echo "Error: Working tree is not clean. Commit or stash your changes before cutting a release." >&2
    exit 1
  fi
fi

EXISTING_TAGS="$(git -C "${REPO_ROOT}" tag -l 'desktop-v*' || true)"

VERSION_INFO="$(PKG_JSON="${PKG_JSON}" EXISTING_TAGS="${EXISTING_TAGS}" BUMP="${BUMP}" node -e '
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync(process.env.PKG_JSON, "utf8"));
const parseSemver = (v) => {
  const m = String(v || "").trim().match(/^(\d+)\.(\d+)\.(\d+)$/);
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
};
const cmpSemver = (a, b) => {
  for (let i = 0; i < 3; i += 1) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
};

const pkgVer = parseSemver(pkg.version);
if (!pkgVer) {
  console.error("Invalid package.json version:", pkg.version);
  process.exit(1);
}

let base = pkgVer;
for (const line of String(process.env.EXISTING_TAGS || "").split(/\r?\n/)) {
  const tag = line.trim();
  if (!tag) continue;
  const parsed = parseSemver(tag.replace(/^desktop-v/, ""));
  if (parsed && cmpSemver(parsed, base) > 0) {
    base = parsed;
  }
}

let [maj, min, pat] = base;
if (process.env.BUMP === "major") {
  maj += 1;
  min = 0;
  pat = 0;
} else if (process.env.BUMP === "minor") {
  min += 1;
  pat = 0;
} else {
  pat += 1;
}

const baseStr = base.join(".");
const nextStr = `${maj}.${min}.${pat}`;
console.log(`${pkg.version}|${baseStr}|${nextStr}`);
')"

IFS='|' read -r PKG_VERSION BASE_VERSION NEW_VERSION <<< "${VERSION_INFO}"
TAG="desktop-v${NEW_VERSION}"

if git -C "${REPO_ROOT}" rev-parse -q --verify "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "Error: Git tag '${TAG}' already exists." >&2
  exit 1
fi

REMOTE_URL="$(git -C "${REPO_ROOT}" remote get-url "${REMOTE}" 2>/dev/null || true)"
GITHUB_BASE_URL="$(REMOTE_URL="${REMOTE_URL}" node -e '
const raw = String(process.env.REMOTE_URL || "").trim();
let m = raw.match(/^https?:\/\/github\.com\/([^/]+)\/(.+?)(?:\.git)?\/?$/i);
if (!m) m = raw.match(/^git@github\.com:([^/]+)\/(.+?)(?:\.git)?$/i);
if (m) console.log(`https://github.com/${m[1]}/${m[2]}`);
')"

if [ "${DRY_RUN}" = "1" ]; then
  echo "Book Studio Desktop release (DRY RUN)"
  echo "  package.json version : ${PKG_VERSION}"
  echo "  highest base version : ${BASE_VERSION}"
  echo "  next version (${BUMP}): ${NEW_VERSION}"
  echo "  release tag          : ${TAG}"
  echo "  branch / remote      : ${BRANCH} -> ${REMOTE}"
  echo ""
  echo "Commands that would run:"
  if [ "${SKIP_CHECKS}" != "1" ]; then
    echo "  (cd studio-desktop && npm run typecheck && npm test)"
  fi
  echo "  (cd studio-desktop && npm version ${NEW_VERSION} --no-git-tag-version --ignore-scripts)"
  echo "  git add studio-desktop/package.json studio-desktop/package-lock.json"
  echo "  git commit -m \"Release Book Studio Desktop ${TAG}\""
  echo "  git tag -a \"${TAG}\" -m \"Book Studio Desktop ${TAG}\""
  echo "  git push ${REMOTE} ${BRANCH} ${TAG}"
  if [ -n "${GITHUB_BASE_URL}" ]; then
    echo ""
    echo "Releases page: ${GITHUB_BASE_URL}/releases"
  fi
  exit 0
fi

if [ "${SKIP_CHECKS}" != "1" ]; then
  echo "Running typecheck and unit tests in studio-desktop/..."
  (cd "${DESKTOP_DIR}" && npm run typecheck && npm test)
fi

echo "Bumping version ${PKG_VERSION} -> ${NEW_VERSION}..."
(cd "${DESKTOP_DIR}" && npm version "${NEW_VERSION}" --no-git-tag-version --ignore-scripts)

git -C "${REPO_ROOT}" add studio-desktop/package.json studio-desktop/package-lock.json
git -C "${REPO_ROOT}" commit -m "Release Book Studio Desktop ${TAG}"
git -C "${REPO_ROOT}" tag -a "${TAG}" -m "Book Studio Desktop ${TAG}"

echo "Pushing ${BRANCH} and ${TAG} to ${REMOTE}..."
git -C "${REPO_ROOT}" push "${REMOTE}" "${BRANCH}" "${TAG}"

echo ""
echo "Release ${TAG} pushed!"
if [ -n "${GITHUB_BASE_URL}" ]; then
  echo "  Actions build : ${GITHUB_BASE_URL}/actions/workflows/desktop-installers.yml"
  echo "  Releases page : ${GITHUB_BASE_URL}/releases/tag/${TAG}"
fi
