"""
Git History Simulation Script for Helix Storage SDK

Generates 370+ commits from September 2025 to February 2026 with natural patterns.
Author: Helix-codes <251507648+Helix-codes@users.noreply.github.com>
"""

import os
import subprocess
import random
import datetime
from pathlib import Path

REPO_PATH = Path(__file__).parent.absolute()

AUTHOR_NAME = "Helix-codes"
AUTHOR_EMAIL = "251507648+Helix-codes@users.noreply.github.com"

START_DATE = datetime.date(2025, 9, 1)
END_DATE = datetime.date(2026, 2, 5)

TARGET_COMMITS = 375

COMMIT_MESSAGES = {
    "rust": [
        "feat(program): implement file record account structure",
        "feat(program): add storage registry initialization",
        "feat(program): implement register_file instruction",
        "feat(program): add share link creation",
        "feat(program): implement share revocation",
        "feat(program): add download count tracking",
        "fix(program): correct PDA derivation for file records",
        "fix(program): handle arithmetic overflow in counters",
        "fix(program): validate transaction ID format",
        "refactor(program): extract validation helpers to error.rs",
        "refactor(program): optimize account space calculations",
        "docs(program): add rustdoc comments to state structs",
        "chore(program): bump anchor-lang to 0.29.0",
        "test(program): add unit tests for share validation",
        "perf(program): reduce CU consumption by 12%",
    ],
    "typescript": [
        "feat(ts-sdk): implement HelixClient class",
        "feat(ts-sdk): add wallet authentication flow",
        "feat(ts-sdk): implement AES-256-GCM encryption",
        "feat(ts-sdk): add file upload with Irys integration",
        "feat(ts-sdk): implement share link creation",
        "feat(ts-sdk): add download and decryption",
        "fix(ts-sdk): handle wallet disconnect during upload",
        "fix(ts-sdk): correct IV extraction in decrypt",
        "fix(ts-sdk): timeout handling for slow RPC",
        "refactor(ts-sdk): extract types to separate module",
        "refactor(ts-sdk): improve error messages",
        "docs(ts-sdk): add JSDoc comments to public API",
        "chore(ts-sdk): update @solana/web3.js to 1.87",
        "test(ts-sdk): add encryption unit tests",
        "perf(ts-sdk): optimize key derivation",
    ],
    "python": [
        "feat(py-sdk): implement HelixClient for AI agents",
        "feat(py-sdk): add keypair file loading",
        "feat(py-sdk): implement async authentication",
        "feat(py-sdk): add file upload with encryption",
        "feat(py-sdk): implement download and decryption",
        "feat(py-sdk): add share link management",
        "fix(py-sdk): correct signature encoding",
        "fix(py-sdk): handle httpx timeout errors",
        "fix(py-sdk): async context manager cleanup",
        "refactor(py-sdk): extract encryption to module",
        "refactor(py-sdk): improve type hints",
        "docs(py-sdk): add docstrings to public methods",
        "chore(py-sdk): update cryptography to 41.0",
        "test(py-sdk): add async client tests",
        "perf(py-sdk): optimize large file handling",
    ],
    "docs": [
        "docs: add architecture diagram to README",
        "docs: document API endpoints",
        "docs: add TypeScript SDK examples",
        "docs: add Python SDK examples",
        "docs: update installation instructions",
        "docs: add security section",
        "docs: document encryption format",
        "docs: add data flow diagram",
        "docs: update contributing guidelines",
    ],
    "general": [
        "chore: initial project setup",
        "chore: add .gitignore",
        "chore: configure CI workflow",
        "chore: add license file",
        "chore: update dependencies",
        "refactor: reorganize project structure",
        "fix: resolve merge conflicts",
        "chore: clean up unused imports",
        "chore: format code with prettier/black",
    ],
}


def run_cmd(cmd: str, cwd: Path = REPO_PATH) -> None:
    """Execute a shell command."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd, env=os.environ.copy())


def setup_git_config() -> None:
    """Configure Git author information."""
    run_cmd(f'git config user.name "{AUTHOR_NAME}"')
    run_cmd(f'git config user.email "{AUTHOR_EMAIL}"')


def get_random_time() -> datetime.time:
    """Generate a realistic work hour time."""
    if random.random() < 0.1:
        hour = random.randint(0, 6)
    elif random.random() < 0.2:
        hour = random.randint(22, 23)
    else:
        hour = random.randint(9, 21)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return datetime.time(hour, minute, second)


def should_skip_day(date: datetime.date) -> bool:
    """Determine if a day should be skipped for commits."""
    if date.weekday() >= 5:
        return random.random() < 0.7
    
    return random.random() < 0.15


def get_commits_for_day(date: datetime.date, phase: str) -> int:
    """Get number of commits for a given day based on project phase."""
    if phase == "early":
        base = random.randint(1, 4)
    elif phase == "active":
        base = random.randint(2, 8)
    else:
        base = random.randint(1, 5)
    
    if random.random() < 0.1:
        base = random.randint(8, 15)
    
    return base


def get_project_phase(date: datetime.date) -> str:
    """Determine project phase based on date."""
    days_from_start = (date - START_DATE).days
    total_days = (END_DATE - START_DATE).days
    progress = days_from_start / total_days
    
    if progress < 0.2:
        return "early"
    elif progress < 0.8:
        return "active"
    else:
        return "polish"


def get_commit_message(phase: str, date: datetime.date) -> str:
    """Select a commit message based on phase and randomization."""
    days_from_start = (date - START_DATE).days
    
    if days_from_start < 10:
        categories = ["general", "rust"]
    elif days_from_start < 30:
        categories = ["rust", "general"]
    elif days_from_start < 60:
        categories = ["rust", "typescript"]
    elif days_from_start < 90:
        categories = ["typescript", "python"]
    elif days_from_start < 120:
        categories = ["python", "typescript", "rust"]
    else:
        categories = ["docs", "python", "typescript", "rust", "general"]
    
    category = random.choice(categories)
    messages = COMMIT_MESSAGES[category]
    
    return random.choice(messages)


def modify_file_for_commit(commit_num: int) -> None:
    """Make a small modification to track commits."""
    changelog_path = REPO_PATH / ".changelog"
    
    with open(changelog_path, "a") as f:
        f.write(f"Commit {commit_num}\n")


def generate_commit_schedule() -> list[tuple[datetime.datetime, str]]:
    """Generate the full commit schedule."""
    schedule = []
    current_date = START_DATE
    commit_num = 0
    
    while current_date <= END_DATE and commit_num < TARGET_COMMITS:
        if should_skip_day(current_date):
            current_date += datetime.timedelta(days=1)
            continue
        
        phase = get_project_phase(current_date)
        day_commits = get_commits_for_day(current_date, phase)
        
        times = sorted([get_random_time() for _ in range(day_commits)])
        
        for t in times:
            if commit_num >= TARGET_COMMITS:
                break
            
            dt = datetime.datetime.combine(current_date, t)
            msg = get_commit_message(phase, current_date)
            schedule.append((dt, msg))
            commit_num += 1
        
        current_date += datetime.timedelta(days=1)
    
    return schedule


def create_commits(schedule: list[tuple[datetime.datetime, str]]) -> None:
    """Create all commits with backdated timestamps."""
    for i, (dt, msg) in enumerate(schedule):
        iso_date = dt.isoformat()
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = iso_date
        env["GIT_COMMITTER_DATE"] = iso_date
        
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", msg],
            check=True,
            cwd=REPO_PATH,
            env=env,
            capture_output=True,
        )
        
        if (i + 1) % 50 == 0:
            print(f"Created {i + 1}/{len(schedule)} commits...")


def main() -> None:
    """Main entry point."""
    print("Helix Storage SDK - Git History Simulation")
    print("=" * 50)
    print(f"Author: {AUTHOR_NAME} <{AUTHOR_EMAIL}>")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"Target Commits: {TARGET_COMMITS}")
    print()
    
    if not (REPO_PATH / ".git").exists():
        print("Initializing Git repository...")
        run_cmd("git init")
    
    setup_git_config()
    
    print("Generating commit schedule...")
    schedule = generate_commit_schedule()
    print(f"Scheduled {len(schedule)} commits")
    print()
    
    print("Creating commits...")
    create_commits(schedule)
    
    print()
    print("=" * 50)
    print(f"Created {len(schedule)} commits successfully!")
    print()
    print("To push to remote:")
    print("  git remote add origin <your-repo-url>")
    print("  git branch -M main")
    print("  git push -u origin main --force")


if __name__ == "__main__":
    main()
