# Building and deploying documentation

## What gets committed

- **Source:** `docs/` (Markdown, API stubs, assets), `mkdocs.yml`, and tutorial notebooks under `notebooks/` (synced into `docs/notebooks/` before a build).
- **Not committed:** `site/` (MkDocs HTML output) and `.cache/` (mkdocs-jupyter cache). Both are listed in `.gitignore`.

## Local preview

```bash
pip install -e ".[docs]"
bash scripts/sync_notebooks_for_docs.sh
mkdocs serve
```

Open the URL MkDocs prints (usually `http://127.0.0.1:8000`).

## GitHub Pages (this repository)

The workflow `.github/workflows/mkdocs-gh-pages.yml` in the repository runs on pushes to `main` and `formal-release`. It installs the package with docs extras, syncs notebooks, and runs `mkdocs gh-deploy --force`, which pushes the built site to the **`gh-pages`** branch.

**Repository settings:** **Settings → Pages → Build and deployment** — source should be **Deploy from a branch**, branch **`gh-pages`**, folder **`/(root)`**. (If you use a different branch or folder, adjust accordingly.)

After the first successful workflow run, the site is available at  
`https://<user-or-org>.github.io/<repo>/` (unless you use a custom domain).

## Updating tutorials

Edit files in `notebooks/`, regenerate or copy into `docs/notebooks/` with `scripts/sync_notebooks_for_docs.sh`, then commit.
