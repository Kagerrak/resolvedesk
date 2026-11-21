"""Explicit local-only bounded live evaluation of the frozen synthetic sample."""

import argparse
from typing import Literal
from uuid import UUID, uuid4

from .database import SessionLocal
from .evaluation import Evaluate, local_live_gate, queue_evaluation
from .evaluation_worker import run_once
from .identity import Identity
from .models import EvaluationRun, Workspace


def execute(
    workspace_id: UUID, method: Literal["exact-cosine-v1", "bm25-v1"], resume: UUID | None = None
):
    local_live_gate()
    with SessionLocal() as db:
        workspace = db.get(Workspace, workspace_id)
        if not workspace or not workspace.demo_owner:
            raise SystemExit("Use an active owned synthetic Admin workspace.")
        if resume:
            run = db.get(EvaluationRun, resume)
            if not run or run.workspace_id != workspace_id or run.mode != "deepseek_sample":
                raise SystemExit("Choose a live evaluation in this exact workspace.")
        else:
            run = queue_evaluation(
                db,
                workspace_id,
                Identity(workspace.demo_owner, True),
                Evaluate(request_id=uuid4(), split="all", method=method),
                live=True,
            )
        run_id = run.id
        db.commit()
    print("Local live evaluation:", run_id, flush=True)
    # A bounded number of case steps; interrupted/leased work is resumed explicitly.
    for _ in range(52):
        with SessionLocal() as db:
            run = db.get(EvaluationRun, run_id)
            if not run or run.status in ("completed", "failed", "cancelled"):
                print("Evaluation status:", run.status if run else "unavailable", flush=True)
                return
        if not run_once(target_run_id=run_id, allow_live=True):
            print("Processing paused. Inspect saved state before an explicit resume.", flush=True)
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_id", type=UUID)
    parser.add_argument(
        "--method", choices=["exact-cosine-v1", "bm25-v1"], default="exact-cosine-v1"
    )
    parser.add_argument("--resume", type=UUID)
    execute(**vars(parser.parse_args()))
