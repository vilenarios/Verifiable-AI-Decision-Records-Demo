from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    app = request.app
    records = app.state.store.list_all()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "records": records,
            "model_info": app.state.model_info,
            "arweave_enabled": app.state.anchor.enabled if app.state.anchor else False,
            "ario_verify_enabled": app.state.ario_verify.enabled if app.state.ario_verify else False,
        },
    )


@router.get("/ui/decisions/{decision_id}", response_class=HTMLResponse)
def decision_detail(request: Request, decision_id: str):
    app = request.app
    envelope = app.state.store.get_by_id(decision_id)

    if not envelope:
        return HTMLResponse("<h1>Decision not found</h1>", status_code=404)

    # Run local verification
    verification = app.state.proof_engine.verify_local(envelope)

    return templates.TemplateResponse(
        request,
        "decision_detail.html",
        {
            "envelope": envelope,
            "verification": verification,
        },
    )
