import os

from fastapi import APIRouter, Header, HTTPException

from ml.evaluation.evaluator import run_evaluation

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

EVAL_SET_PATH = os.getenv("EVAL_SET_PATH", "data/eval_sets/golden_set.json")


@router.post("/run")
async def run_eval(
    x_tenant_id: str = Header(...),
    top_k: int = 5,
):
    """Run evaluation against the golden set. Returns full report."""
    try:
        report = await run_evaluation(
            eval_set_path=EVAL_SET_PATH,
            tenant_id=x_tenant_id,
            top_k=top_k,
        )
        return report
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
