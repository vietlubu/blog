# Repository Guidelines

## Project Overview
This is a personal Hugo blog ("Vietlubu") built on the vendored `terminal` theme. Posts are written in an Obsidian vault on iCloud, copied into `content/posts/` by a local Python script, committed, and then built and deployed to GitHub Pages by CI.

## Architecture & Data Flow
```
Obsidian vault (iCloud) ──sync-obsidian-hugo.py──▶ content/posts/*.md + static/images/*
                                                            │ git push main
                                                            ▼
                        hugo.toml + themes/terminal + layouts/ ──hugo──▶ public/ ──▶ GitHub Pages
```
- Theme templates come from `themes/terminal/`. Files in `layouts/` win over them.
- The only overrides are `layouts/_default/index.html` and `layouts/_default/list.html`. They are copies of the theme files with one change: the list summary is `.Summary | plainify | htmlUnescape | truncate 200`. If you update the theme, apply that change to the new copies again.
- To customize the theme, use its hooks first: `extended_head.html` and `extended_footer.html`. Otherwise copy the theme file into `layouts/` at the same path. Leave `themes/terminal/` itself unedited.
- `themes/terminal/` is plain vendored files, not a git submodule. Updating the theme means re-copying it from upstream.
- The sync script can't run in CI because it reads a local iCloud vault. Content must be synced and committed locally before pushing.

## Key Directories
- `content/posts/`: synced posts. Treat Obsidian as the source of truth, because a full sync overwrites this folder (see Gotchas).
- `static/images/`: images embedded in posts, served at `/images/<name>`.
- `layouts/_default/`: theme overrides.
- `themes/terminal/`: vendored theme. Its `exampleSite/`, `package.json` and lint configs aren't used by this site.
- `archetypes/default.md`: template used by `hugo new`.
- Generated or ignored paths: `public/` (build output), `venv/`, `.env`, `sync.log`. Leave these out of edits and commits.

## Development Commands
```sh
hugo server -D                      # local preview, drafts included
hugo --gc --minify                  # production-like build into public/
hugo new content posts/my-post.md   # new draft post (TOML front matter)

# Obsidian → Hugo sync (run from repo root so .env is found)
source venv/bin/activate
python sync-obsidian-hugo.py                 # full mirror (rsync --delete)
python sync-obsidian-hugo.py "my post.md"    # one file, path relative to OBSIDIAN_POSTS_DIR, no deletes
```
- There is no Makefile, no `package.json` and no `requirements.txt`. The venv needs `python-dotenv`, plus `rsync` on PATH.

## Code Conventions & Common Patterns
- **Post filenames** follow `N. kebab-name.md`, e.g. `1. test-post.md`. The numeric prefix and space come from the Obsidian naming. No posts set `slug` or `url`, and there is no `[permalinks]` block, so URLs are derived from the filename.
- **Front matter** is YAML, written in Obsidian:
  ```yaml
  ---
  title: test post
  date: 2025-05-24
  draft: false
  tags:
    - blog
  ---
  ```
  `archetypes/default.md` produces TOML (`+++`) instead. Use YAML for consistency, since the sync script never touches front matter. Posts with `draft: true` are left out of production builds.
- **Images**: the Obsidian embed `![[Pasted image 20250524212810.png]]` is rewritten by `process_images()` to `![Pasted image 20250524212810.png](/images/Pasted%20image%2020250524212810.png)`, and the file is copied to `static/images/`. Only spaces are `%20`-encoded.
- **Sync script style** (`sync-obsidian-hugo.py`): flat procedural functions, `sync_posts()` and `process_images()`. Errors are printed rather than raised, and the process exits 0 even when a sync fails. The script reads its four env vars at import time and calls `exit(1)` if any is empty: `OBSIDIAN_POSTS_DIR`, `HUGO_POSTS_DIR`, `OBSIDIAN_ATTACHMENTS_DIR`, `HUGO_STATIC_IMAGES_DIR`. The template is `.env.example`, and `.env` holds machine-specific absolute paths.
- **Config**: `hugo.toml` uses the lowercase key `baseurl = "/"`, which CI overrides. It defines a single language, `[languages.vi]`, with English UI strings. The logo lives under `languages.vi.*`, and there is no main menu. There is no `en` language, no `i18n/`, and no custom taxonomies, so the default `tags` and `categories` apply.

## Important Files
- `hugo.toml`: site config and theme params (`contentTypeName = "posts"`, `autoCover = true`, `pagination.pagerSize = 5`, `markup.highlight.noClasses = false`).
- `.github/workflows/hugo.yaml`: the build and Pages deploy workflow.
- `sync-obsidian-hugo.py`: the content pipeline.
- `layouts/_default/index.html`, `layouts/_default/list.html`: list templates with the truncated summary.

## Runtime/Tooling Preferences
- **Hugo extended 0.147.2** is pinned in the workflow's `HUGO_VERSION`; bump it there. Match that version locally. The theme needs at least 0.90, but `pagination.pagerSize` requires a modern Hugo.
- **Python 3.11** venv at `venv/`, Homebrew python@3.11.
- **CI** runs on push to `main` or by manual dispatch, and pull requests don't build. It runs `hugo --gc --minify --baseURL "<pages url>/"` with `HUGO_ENVIRONMENT=production` and `TZ=America/Los_Angeles`.

## Testing & QA
- There are no tests, linters, formatters or link checkers, and CI only builds and deploys.
- To verify a change, run `hugo --gc --minify` and check that it finishes without errors or warnings, then look at the affected pages in `hugo server -D`.
- For sync script changes, test against a scratch `HUGO_POSTS_DIR` first, because a full sync deletes files.

## Commit Workflow
- Commit as soon as each task is done and verified (see Testing & QA). One commit per logical change; leave nothing uncommitted at the end of a task.
- Stage only the files the task touched (`git add <paths>`), never `git add -A`: the worktree may hold the user's unrelated edits.
- Message style follows history: short lowercase imperative subject, e.g. `add sample post`, `add custom js code`, `update sync image regex`.
- Commit locally only; pushing to `main` triggers a production deploy, so push only when the user asks.

## Gotchas
- A full sync runs `rsync -av --delete <vault>/ content/posts`. Any post that exists only in `content/posts/` is **deleted**. Single-file mode doesn't delete.
- `process_images` only matches `.png` embeds, through the regex `!\[\[(.*?\.png)\]\]`. It leaves these alone:
  - `.jpg`, `.gif` and `.webp` embeds
  - `![[x.png|300]]` size syntax
  - plain `[[wikilinks]]`
- Images are never removed from `static/images/`, and a new image with the same name silently overwrites the old one.
- If an image can't be found, the script prints a warning but still rewrites the link.
- Files are opened without `encoding="utf-8"`. Vietnamese text depends on the locale being UTF-8.
- `.hugo_build.lock` is tracked in git even though Hugo regenerates it.
