from workers.celery_app import celery_app
from api.routes.ws import emit_event
import structlog
import uuid
from datetime import datetime, timezone

log = structlog.get_logger()


@celery_app.task(bind=True, name="workers.scan_worker.run_scan_task")
def run_scan_task(self, scan_id: str, zip_path: str = None):
    """
    Full scan pipeline:
    1. Ingest repo / zip
    2. AST scan (red)
    3. Ghost commit scan (red)
    4. Chain builder (red)
    5. PoC generation (red)
    6. Patch generation (blue)
    7. Patch validation loop (blue)
    8. Threat actor profiling
    9. Scoring
    10. Save results
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from models.scan import Scan, ScanStatus
    from config import settings

    engine = create_engine(settings.DATABASE_URL)

    def update_scan(session, **kwargs):
        session.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).update(kwargs)
        session.commit()

    def emit(stage, message, data=None, progress=0):
        emit_event(scan_id, stage, message, data, progress)

    with Session(engine) as session:
        scan = session.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
        if not scan:
            log.error("Scan not found", scan_id=scan_id)
            return

        try:
            # ── Phase 1: Ingestion ─────────────────────────────────────────
            update_scan(session, status=ScanStatus.INGESTING)
            emit("ingesting", "Cloning repository...", progress=5)

            files = []
            repo_path = None

            if scan.github_url:
                from engines.ingestion.github_ingest import RepoIngestion
                ingestor = RepoIngestion(scan.github_url)
                repo_path = ingestor.clone()
                files = ingestor.get_files()
                repo_name = ingestor.get_repo_name()
                update_scan(session, repo_name=repo_name)
            elif zip_path:
                from engines.ingestion.zip_ingest import ZipIngestion
                ingestor = ZipIngestion(zip_path)
                ingestor.extract()
                files = ingestor.get_files()
                repo_path = ingestor.extract_path

            emit("ingesting", f"Loaded {len(files)} files", progress=10)

            # ── Phase 2: AST Scan ──────────────────────────────────────────
            update_scan(session, status=ScanStatus.SCANNING)
            emit("scanning", "Running vulnerability scanner...", progress=20)

            from engines.red.ast_scanner import scan_files
            findings = scan_files(files)

            # Tag findings with IDs
            for i, f in enumerate(findings):
                f["id"] = f"finding_{i+1}"

            # Live URL probe if applicable
            if scan.live_url:
                from engines.ingestion.live_probe import probe_live_url
                import asyncio
                live_findings = asyncio.run(probe_live_url(scan.live_url))
                for i, f in enumerate(live_findings):
                    f["id"] = f"live_finding_{i+1}"
                findings.extend(live_findings)

            emit("scanning", f"Found {len(findings)} vulnerabilities", {"count": len(findings)}, progress=35)

            # ── Phase 3: Ghost Commit Scan ─────────────────────────────────
            ghost_commits = []
            if repo_path:
                emit("ghost_commit", "Scanning git history for secrets...", progress=40)
                from engines.red.ghost_commit import scan_git_history
                ghost_commits = scan_git_history(repo_path)
                emit("ghost_commit", f"Found {len(ghost_commits)} historical secrets", {"count": len(ghost_commits)}, progress=45)

            # ── Phase 4: Chain Builder ─────────────────────────────────────
            update_scan(session, status=ScanStatus.CHAINING)
            emit("chaining", "Building vulnerability call graph...", progress=50)

            from engines.red.chain_builder import build_call_graph, find_vuln_chains, build_graph_data_for_ui
            G = build_call_graph(files, findings)
            chains = find_vuln_chains(G)
            graph_data = build_graph_data_for_ui(G, chains)

            emit("chaining", f"Discovered {len(chains)} exploit chains", {"chains": len(chains)}, progress=58)

            # ── Phase 5: PoC Generation ────────────────────────────────────
            update_scan(session, status=ScanStatus.GENERATING)
            emit("generating", "Generating proof-of-concept exploits...", progress=62)

            from engines.red.poc_generator import PoCGenerator
            poc_gen = PoCGenerator()
            for finding in findings[:10]:  # cap PoC gen to top 10 to save time
                if finding.get("severity") in ("critical", "high"):
                    poc = poc_gen.generate_poc(finding)
                    if poc:
                        finding["poc_exploit"] = poc

            emit("generating", "PoC exploits generated", progress=68)

            # ── Phase 6: Patch Generation ──────────────────────────────────
            update_scan(session, status=ScanStatus.PATCHING)
            emit("patching", "Generating security patches...", progress=72)

            from engines.blue.patch_generator import PatchGenerator
            patch_gen = PatchGenerator()
            patches = patch_gen.patch_all_findings(findings, files)

            emit("patching", f"Generated {len(patches)} patches", progress=78)

            # ── Phase 7: Patch Validation ──────────────────────────────────
            emit("validating", "Red agent validating patches...", progress=82)

            from engines.blue.patch_validator import PatchValidator
            validator = PatchValidator()
            validated_patches = validator.validate_all(findings, patches)
            verified_count = sum(1 for p in validated_patches if p.get("validated"))

            emit("validating", f"{verified_count}/{len(validated_patches)} patches verified", progress=87)

            # ── Phase 8: Threat Profiling ──────────────────────────────────
            emit("profiling", "Matching threat actor profiles...", progress=90)
            from engines.red.threat_profiler import match_threat_actors
            threat_actor = match_threat_actors(findings)
            if threat_actor:
                emit("profiling", f"Matched: {threat_actor['name']}", {"actor": threat_actor["name"]}, progress=92)

            # ── Phase 9: Security Headers ──────────────────────────────────
            from engines.blue.header_fixer import detect_framework, generate_header_config
            framework = detect_framework(files)
            header_config = generate_header_config(framework)

            # ── Phase 10: Scoring ──────────────────────────────────────────
            update_scan(session, status=ScanStatus.SCORING)
            from engines.scoring.scorer import calculate_score, calculate_score_after_patches

            score_before = calculate_score(findings, chains, ghost_commits, len(files))
            score_after = calculate_score_after_patches(score_before, validated_patches, findings)

            emit("scoring", f"Score: {score_before} → {score_after}", {"before": score_before, "after": score_after}, progress=96)

            # ── Save All Results ───────────────────────────────────────────
            critical = sum(1 for f in findings if f.get("severity") == "critical")
            high = sum(1 for f in findings if f.get("severity") == "high")
            medium = sum(1 for f in findings if f.get("severity") == "medium")
            low = sum(1 for f in findings if f.get("severity") == "low")

            update_scan(session,
                status=ScanStatus.COMPLETE,
                total_findings=len(findings),
                critical_count=critical,
                high_count=high,
                medium_count=medium,
                low_count=low,
                score_before=score_before,
                score_after=score_after,
                findings_data=findings,
                chains_data=chains,
                patches_data=validated_patches,
                ghost_commits_data=ghost_commits,
                threat_actor_data=threat_actor,
                attack_graph_data=graph_data,
                completed_at=datetime.now(timezone.utc),
            )

            emit("complete", "Scan complete!", {
                "score_before": score_before,
                "score_after": score_after,
                "total_findings": len(findings),
                "chains": len(chains),
            }, progress=100)

            # Cleanup
            if scan.github_url and repo_path:
                ingestor.cleanup()

        except Exception as e:
            log.error("Scan pipeline failed", scan_id=scan_id, error=str(e))
            update_scan(session, status=ScanStatus.FAILED)
            emit("failed", f"Scan failed: {str(e)}", progress=0)
            raise
