import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.celery_app import celery_app
import structlog
import uuid
from datetime import datetime

log = structlog.get_logger()


def emit(scan_id: str, stage: str, message: str, data: dict = None, progress: int = 0):
    """Push event to Redis for WebSocket to pick up."""
    try:
        import redis, json
        r = redis.from_url("redis://localhost:6379/0")
        event = {
            "scan_id": scan_id,
            "stage": stage,
            "message": message,
            "progress": progress,
            "data": data or {},
        }
        r.publish(f"scan:{scan_id}:events", json.dumps(event))
        r.close()
    except Exception as e:
        log.warning("Could not emit event", error=str(e))


@celery_app.task(bind=True, name="workers.scan_worker.run_scan_task")
def run_scan_task(self, scan_id: str, zip_path: str = None):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from models.scan import Scan, ScanStatus

    # Use sync SQLite engine in the worker
    engine = create_engine(
        "sqlite:///./codesentinel.db",
        connect_args={"check_same_thread": False},
    )

    def update_scan(session, **kwargs):
        session.query(Scan).filter(Scan.id == scan_id).update(kwargs)
        session.commit()

    with Session(engine) as session:
        scan = session.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            log.error("Scan not found", scan_id=scan_id)
            return

        try:
            # ── Phase 1: Ingestion ─────────────────────────────────
            update_scan(session, status=ScanStatus.INGESTING.value)
            emit(scan_id, "ingesting", "Cloning repository...", progress=5)

            files = []
            repo_path = None

            if scan.github_url:
                from engines.ingestion.github_ingest import RepoIngestion
                ingestor = RepoIngestion(scan.github_url)
                repo_path = ingestor.clone()
                files = ingestor.get_files()
                repo_name = ingestor.get_repo_name()
                update_scan(session, repo_name=repo_name)
                emit(scan_id, "ingesting", f"Loaded {len(files)} files", progress=10)

            elif zip_path:
                from engines.ingestion.zip_ingest import ZipIngestion
                ingestor = ZipIngestion(zip_path)
                ingestor.extract()
                files = ingestor.get_files()
                repo_path = ingestor.extract_path
                emit(scan_id, "ingesting", f"Loaded {len(files)} files from ZIP", progress=10)

            # ── Phase 2: AST Scan ──────────────────────────────────
            update_scan(session, status=ScanStatus.SCANNING.value)
            emit(scan_id, "scanning", "Running vulnerability scanner...", progress=20)

            from engines.red.ast_scanner import scan_files
            findings = scan_files(files)

            for i, f in enumerate(findings):
                f["id"] = f"finding_{i+1}"

            # Live URL probe
            if scan.live_url:
                try:
                    import asyncio
                    from engines.ingestion.live_probe import probe_live_url
                    live_findings = asyncio.run(probe_live_url(scan.live_url))
                    for i, f in enumerate(live_findings):
                        f["id"] = f"live_{i+1}"
                    findings.extend(live_findings)
                except Exception as e:
                    log.warning("Live probe failed", error=str(e))

            emit(scan_id, "scanning", f"Found {len(findings)} vulnerabilities",
                 {"count": len(findings)}, progress=35)

            # ── Phase 3: Ghost Commit Scan ─────────────────────────
            ghost_commits = []
            if repo_path:
                emit(scan_id, "ghost_commit", "Scanning git history for secrets...", progress=40)
                try:
                    from engines.red.ghost_commit import scan_git_history
                    ghost_commits = scan_git_history(repo_path)
                    emit(scan_id, "ghost_commit",
                         f"Found {len(ghost_commits)} historical secrets",
                         {"count": len(ghost_commits)}, progress=45)
                except Exception as e:
                    log.warning("Ghost commit scan failed", error=str(e))
                    emit(scan_id, "ghost_commit", "Git history scan skipped", progress=45)

            # ── Phase 4: Chain Builder ─────────────────────────────
            update_scan(session, status=ScanStatus.CHAINING.value)
            emit(scan_id, "chaining", "Building vulnerability call graph...", progress=50)

            chains = []
            graph_data = {"nodes": [], "edges": []}
            try:
                from engines.red.chain_builder import (
                    build_call_graph, find_vuln_chains, build_graph_data_for_ui
                )
                G = build_call_graph(files, findings)
                chains = find_vuln_chains(G)
                graph_data = build_graph_data_for_ui(G, chains)
                emit(scan_id, "chaining",
                     f"Discovered {len(chains)} exploit chains",
                     {"chains": len(chains)}, progress=58)
            except Exception as e:
                log.warning("Chain builder failed", error=str(e))
                emit(scan_id, "chaining", "Chain analysis skipped", progress=58)

            # ── Phase 5: PoC Generation ────────────────────────────
            update_scan(session, status=ScanStatus.GENERATING.value)
            emit(scan_id, "generating", "Generating proof-of-concept exploits...", progress=62)

            try:
                from engines.red.poc_generator import PoCGenerator
                import time
                poc_gen = PoCGenerator()
                critical_findings = [f for f in findings if f.get("severity") in ("critical", "high")]
                for finding in critical_findings[:5]:  # cap at 5 to save API calls
                    poc = poc_gen.generate_poc(finding)
                    if poc:
                        finding["poc_exploit"] = poc
                    time.sleep(3) # Throttle to respect Groq API rate limits
                emit(scan_id, "generating", "PoC exploits generated", progress=68)
            except Exception as e:
                log.warning("PoC generation failed", error=str(e))
                emit(scan_id, "generating", "PoC generation skipped (check GROQ_API_KEY)", progress=68)

            # ── Phase 6: Patch Generation ──────────────────────────
            update_scan(session, status=ScanStatus.PATCHING.value)
            emit(scan_id, "patching", "Generating security patches...", progress=72)

            patches = []
            try:
                from engines.blue.patch_generator import PatchGenerator
                patch_gen = PatchGenerator()
                patches = patch_gen.patch_all_findings(findings, files)
                emit(scan_id, "patching",
                     f"Generated {len(patches)} patches", progress=78)
            except Exception as e:
                log.warning("Patch generation failed", error=str(e))
                emit(scan_id, "patching", "Patch generation skipped", progress=78)

            # ── Phase 7: Patch Validation ──────────────────────────
            emit(scan_id, "validating", "Red agent validating patches...", progress=82)

            validated_patches = patches  # skip validation if no patches
            try:
                if patches:
                    from engines.blue.patch_validator import PatchValidator
                    validator = PatchValidator()
                    validated_patches = validator.validate_all(findings, patches)
                    verified = sum(1 for p in validated_patches if p.get("validated"))
                    emit(scan_id, "validating",
                         f"{verified}/{len(validated_patches)} patches verified", progress=87)
            except Exception as e:
                log.warning("Patch validation failed", error=str(e))
                emit(scan_id, "validating", "Validation skipped", progress=87)

            # ── Phase 8: Threat Profiling ──────────────────────────
            emit(scan_id, "profiling", "Matching threat actor profiles...", progress=90)
            threat_actor = None
            try:
                from engines.red.threat_profiler import match_threat_actors
                threat_actor = match_threat_actors(findings)
                if threat_actor:
                    emit(scan_id, "profiling",
                         f"Matched: {threat_actor['name']}", progress=92)
                else:
                    emit(scan_id, "profiling", "No specific threat actor matched", progress=92)
            except Exception as e:
                log.warning("Threat profiling failed", error=str(e))

            # ── Phase 9: Scoring ───────────────────────────────────
            update_scan(session, status=ScanStatus.SCORING.value)
            emit(scan_id, "scoring", "Calculating security score...", progress=95)

            from engines.scoring.scorer import calculate_score, calculate_score_after_patches
            score_before = calculate_score(findings, chains, ghost_commits, len(files))
            score_after = calculate_score_after_patches(score_before, validated_patches, findings)

            emit(scan_id, "scoring",
                 f"Score: {score_before} → {score_after}",
                 {"before": score_before, "after": score_after}, progress=97)

            # ── Save Results ───────────────────────────────────────
            critical = sum(1 for f in findings if f.get("severity") == "critical")
            high = sum(1 for f in findings if f.get("severity") == "high")
            medium = sum(1 for f in findings if f.get("severity") == "medium")
            low = sum(1 for f in findings if f.get("severity") == "low")

            import json
            update_scan(session,
                status=ScanStatus.COMPLETE.value,
                total_findings=len(findings),
                critical_count=critical,
                high_count=high,
                medium_count=medium,
                low_count=low,
                score_before=score_before,
                score_after=score_after,
                findings_data=json.dumps(findings),
                chains_data=json.dumps(chains),
                patches_data=json.dumps(validated_patches),
                ghost_commits_data=json.dumps(ghost_commits),
                threat_actor_data=json.dumps(threat_actor) if threat_actor else None,
                attack_graph_data=json.dumps(graph_data),
                completed_at=datetime.utcnow(),
            )

            emit(scan_id, "complete", "Scan complete!", {
                "score_before": score_before,
                "score_after": score_after,
                "total_findings": len(findings),
                "chains": len(chains),
            }, progress=100)

            log.info("Scan complete", scan_id=scan_id,
                     findings=len(findings), score=f"{score_before}→{score_after}")

            # Cleanup cloned repo
            try:
                if scan.github_url and repo_path:
                    ingestor.cleanup()
            except Exception:
                pass

        except Exception as e:
            log.error("Scan pipeline failed", scan_id=scan_id, error=str(e))
            import traceback
            traceback.print_exc()
            try:
                update_scan(session,
                    status=ScanStatus.FAILED.value,
                    completed_at=datetime.utcnow(),
                )
            except Exception:
                pass
            emit(scan_id, "failed", f"Scan failed: {str(e)}", progress=0)
            raise