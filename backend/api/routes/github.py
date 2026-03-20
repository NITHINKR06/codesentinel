from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import json

from db.database import get_db
from models.scan import Scan
from config import settings

router = APIRouter()


class PRRequest(BaseModel):
    scan_id: str
    repo_url: str
    branch_name: str = "codesentinel/security-fixes"


@router.post("/pr")
async def create_pull_request(request: PRRequest, db: AsyncSession = Depends(get_db)):
    if not settings.GITHUB_TOKEN:
        raise HTTPException(400, "GITHUB_TOKEN not configured on server")

    result = await db.execute(select(Scan).where(Scan.id == request.scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")

    def parse(field):
        if not field:
            return []
        if isinstance(field, str):
            try:
                return json.loads(field)
            except Exception:
                return []
        return field

    patches_data = parse(scan.patches_data)
    findings_data = parse(scan.findings_data)
    chains_data = parse(scan.chains_data)

    try:
        attack_graph = scan.attack_graph_data
        if isinstance(attack_graph, str):
            attack_graph = json.loads(attack_graph)
        simulation_results = attack_graph.get("simulations", []) if isinstance(attack_graph, dict) else []
    except Exception:
        simulation_results = []

    validated_patches = [p for p in patches_data if p.get("validated")]
    if not validated_patches:
        raise HTTPException(400, "No validated patches available — run a scan first")

    # Capture scalar values before any async ops
    score_before = scan.score_before or 0
    score_after = scan.score_after or 0
    github_url = scan.github_url or ""

    try:
        from github import Github, GithubException, Auth
        from engines.blue.surgical_patch import apply_surgical_patch, build_pr_body

        auth = Auth.Token(settings.GITHUB_TOKEN)
        g = Github(auth=auth)

        repo_path = request.repo_url.replace("https://github.com/", "").rstrip("/").removesuffix(".git")
        target_repo = g.get_repo(repo_path)
        default_branch = target_repo.default_branch
        
        user = g.get_user()
        has_push = getattr(target_repo.permissions, "push", False)

        if has_push:
            repo = target_repo
            head = request.branch_name
            source = repo.get_branch(default_branch)
        else:
            repo = user.create_fork(target_repo)
            
            # Wait for fork to be ready and branch to exist
            import time
            for _ in range(10):
                try:
                    source = repo.get_branch(default_branch)
                    break
                except Exception:
                    time.sleep(2)
            else:
                source = repo.get_branch(default_branch)
            
            head = f"{user.login}:{request.branch_name}"

        # Create branch
        try:
            repo.create_git_ref(
                ref=f"refs/heads/{request.branch_name}",
                sha=source.commit.sha,
            )
        except GithubException as e:
            if e.status != 422:
                raise

        # Finding map for line number lookup
        finding_map = {}
        for f in findings_data:
            finding_map.setdefault(f.get("file_path", ""), []).append(f)

        applied = []
        skipped = []

        for patch in validated_patches:
            file_path = patch.get("file_path", "")
            vuln_code = patch.get("original_code", "")
            patch_code = patch.get("patched_code", "")

            if not file_path or not patch_code:
                skipped.append({"file": file_path, "reason": "Missing file path or patch code"})
                continue

            try:
                contents = repo.get_contents(file_path, ref=request.branch_name)
                original_content = contents.decoded_content.decode("utf-8")
                file_sha = contents.sha
            except GithubException as e:
                skipped.append({"file": file_path, "reason": f"File not found: {e.status}"})
                continue
            except Exception as e:
                skipped.append({"file": file_path, "reason": str(e)})
                continue

            # Get line number from findings
            line_number = None
            for f in finding_map.get(file_path, []):
                if f.get("vuln_type") == patch.get("vuln_type"):
                    line_number = f.get("line_number")
                    break

            # Apply surgical patch
            patched_content, success, description = apply_surgical_patch(
                original_content=original_content,
                vulnerable_code=vuln_code,
                patched_code=patch_code,
                line_number=line_number,
            )

            if not success:
                skipped.append({"file": file_path, "reason": description})
                continue

            if patched_content == original_content:
                skipped.append({"file": file_path, "reason": "No change detected — already patched"})
                continue

            try:
                repo.update_file(
                    path=file_path,
                    message=f"fix(security): patch {patch.get('vuln_type', 'vulnerability')} in {file_path}",
                    content=patched_content,
                    sha=file_sha,
                    branch=request.branch_name,
                )
                applied.append({
                    "file": file_path,
                    "vuln_type": patch.get("vuln_type"),
                    "description": description,
                })
            except Exception as e:
                skipped.append({"file": file_path, "reason": str(e)})

        if not applied:
            raise HTTPException(
                400,
                f"No patches could be applied. "
                f"{len(skipped)} skipped: {'; '.join(s['reason'] for s in skipped[:3])}"
            )

        # Build PR body without touching scan ORM object
        sev_counts = {
            "critical": sum(1 for f in findings_data if f.get("severity") == "critical"),
            "high": sum(1 for f in findings_data if f.get("severity") == "high"),
            "medium": sum(1 for f in findings_data if f.get("severity") == "medium"),
            "low": sum(1 for f in findings_data if f.get("severity") == "low"),
        }

        findings_table = "\n".join(
            f"| `{f.get('file_path','')}:{f.get('line_number','')}` "
            f"| {f.get('severity','').upper()} "
            f"| {f.get('title','')} |"
            for f in findings_data[:15]
        )

        patches_list = "\n".join(
            f"- ✅ `{p['file']}` — {p.get('vuln_type','')} ({p.get('description','')})"
            for p in applied
        )

        sim_section = ""
        if simulation_results:
            confirmed = [s for s in simulation_results if s.get("confirmed")]
            if confirmed:
                sim_section = f"\n### 🔴 Live Simulation\n{len(confirmed)}/{len(simulation_results)} exploits confirmed before patching.\n"

        pr_body = f"""## 🛡️ CodeSentinel — Automated Security Report

> Surgical patches — only vulnerable lines modified. Surrounding code untouched.

### 📊 Score
| Before | After |
|--------|-------|
| **{score_before}** / 100 | **{score_after}** / 100 |

### 🔍 Severity Breakdown
| 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low |
|------------|---------|----------|--------|
| {sev_counts['critical']} | {sev_counts['high']} | {sev_counts['medium']} | {sev_counts['low']} |

### 📁 Findings
| File | Severity | Type |
|------|----------|------|
{findings_table}

### 🔧 Patches Applied ({len(applied)})
{patches_list}
{sim_section}
---
*Generated by [CodeSentinel](https://github.com/NITHINKR06/codesentinel)*
"""

        pr = target_repo.create_pull(
            title=f"[CodeSentinel] {len(applied)} surgical security patch(es)",
            body=pr_body,
            head=head,
            base=default_branch,
        )

        # Update scan with PR info
        await db.execute(
            Scan.__table__.update()
            .where(Scan.id == request.scan_id)
            .values(pr_url=pr.html_url, pr_number=pr.number)
        )
        await db.commit()

        return {
            "pr_url": pr.html_url,
            "pr_number": pr.number,
            "files_patched": len(applied),
            "files_skipped": len(skipped),
            "patches_applied": applied,
            "patches_skipped": skipped,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to create PR: {str(e)}")