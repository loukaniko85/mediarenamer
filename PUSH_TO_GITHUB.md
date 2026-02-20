# How to Push to GitHub

## Quick Start

### Option 1: Using the script (easiest)

```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

The script will:
- Prompt for Git name/email if not set
- Initialize the repo and add the remote if needed
- Stage, commit, and push to `main`

### Option 2: Manual steps

1. **Set Git identity** (required once per machine):

   ```bash
   git config --global user.email "you@example.com"
   git config --global user.name "Your Name"
   ```

   Example (keeps email private on GitHub):

   ```bash
   git config --global user.email "loukaniko85@users.noreply.github.com"
   git config --global user.name "loukaniko85"
   ```

2. **Initialize and push:**

   ```bash
   cd /path/to/mediarenamer
   git init
   git add .
   git commit -m "Initial commit: MediaRenamer"
   git remote add origin https://github.com/loukaniko85/mediarenamer.git
   git branch -M main
   git push -u origin main
   ```

## Remote URL

Use the correct repo URL (username **loukaniko85**, not Loukaniko05):

- HTTPS: `https://github.com/loukaniko85/mediarenamer.git`
- SSH: `git@github.com:loukaniko85/mediarenamer.git`

Check or fix the remote:

```bash
git remote -v
git remote set-url origin https://github.com/loukaniko85/mediarenamer.git
```

## Authentication

GitHub no longer accepts account passwords for Git. Use one of these:

1. **Personal Access Token (PAT)**  
   - GitHub → Settings → Developer settings → Personal access tokens  
   - Create a token with `repo` scope  
   - When `git push` asks for a password, paste the token

2. **SSH key**  
   - Add an SSH key in GitHub → Settings → SSH and GPG keys  
   - Then: `git remote set-url origin git@github.com:loukaniko85/mediarenamer.git`

## Create the repo first (if needed)

If the repository does not exist yet:

1. Go to https://github.com/new  
2. Repository name: `mediarenamer`  
3. Public or Private as you prefer  
4. Do **not** add a README (you already have one)  
5. Create repository, then run the script or manual steps above  

## After pushing

- Workflow runs automatically: https://github.com/loukaniko85/mediarenamer/actions  
- AppImage: download from the workflow run artifacts  
- Docker: `docker pull ghcr.io/loukaniko85/mediarenamer:main`  

## Creating a release

1. GitHub repo → **Releases** → **Create a new release**  
2. Tag (e.g. `v1.0.0`), add notes, publish  
3. The workflow will attach the AppImage to the release  

## Troubleshooting

| Issue | What to do |
|-------|------------|
| **Author identity unknown** | Run the `git config --global user.email` and `user.name` commands above. |
| **Push failed / authentication** | Use a PAT or SSH; ensure remote URL is `loukaniko85` (not Loukaniko05). |
| **No changes to commit** | Run `git status`. If clean, try `git push -u origin main` to sync. |
| **Workflow doesn’t run** | Ensure branch is `main` and `.github/workflows/build.yml` is committed. |
