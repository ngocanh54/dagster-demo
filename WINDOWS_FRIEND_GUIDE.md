# Dagster Demo for Windows (Non-Technical Guide)

This guide is for trying the demo with as little setup as possible.

## What you will do

1. Install Git + WSL
2. Download this repo
3. Run 2 commands
4. Open Dagster in your browser

Total time: about 15-25 minutes.

## Step 1: Install required apps (recommended path)

Install these in this order:

1. Git for Windows
2. WSL (Windows Subsystem for Linux)

### 1) Install Git for Windows

- Download: https://git-scm.com/download/win
- Keep default options during install.

### 2) Install WSL

- Open **PowerShell as Administrator**
- Run:

```powershell
wsl --install
```

- Restart your computer if prompted.
- Open the `Ubuntu` app and finish first-time setup.

## Step 2: Open Ubuntu (WSL)

- Press Start
- Search for `Ubuntu`
- Open it

## Step 3: Download this project

In Ubuntu terminal, run:

```bash
git clone <REPO_URL>
cd dagster_demo
```

Replace `<REPO_URL>` with the repository URL I shared with you.

## Step 4: Install project dependencies

Run:

```bash
make install
```

Wait until it finishes. First run can take a few minutes.

## Step 5: Start Dagster

Run:

```bash
make dev
```

When you see a message with `http://localhost:3000`, keep this terminal open.

## Step 6: Open the Dagster page

Open this in your browser:

- http://localhost:3000

You should see the Dagster UI.

## Step 7: Quick test in UI

1. Open the `Assets` page
2. Click `Materialize all`
3. Wait until runs show success (green)

That confirms the demo is working.

## How to stop

- In the terminal where `make dev` is running, press `Ctrl + C`

## If something fails

Run these checks in Ubuntu terminal and send me the output:

```bash
python --version
make --version
git --version
```

Then run:

```bash
make windows-guide
```

Copy the full output and send it to me.

## Optional: Native Windows path (advanced)

If you do not want WSL, you need:
- Python 3.10+
- GNU Make on Windows (Chocolatey is one way to install it)

Chocolatey is only for this native Windows path. It is not required if using WSL.
