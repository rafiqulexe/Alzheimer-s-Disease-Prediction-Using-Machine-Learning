# core/templates.py
from pathlib import Path
from typing import Any
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

class CompatibleJinja2Templates(Jinja2Templates):
    """
    Subclass that provides full backwards-compatibility between
    Starlette's legacy TemplateResponse("file.html", {"request": req, ...})
    and modern Starlette 0.38+ TemplateResponse(request=req, name="file.html", context={...}).
    """
    def TemplateResponse(self, *args: Any, **kwargs: Any):
        # Format: TemplateResponse("login.html", {"request": request, "message": ""})
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            name = args[0]
            context = args[1]
            request = context.get("request") or kwargs.get("request")
            return super().TemplateResponse(request=request, name=name, context=context, **kwargs)

        # Format: TemplateResponse("login.html", request=request, context={...})
        elif len(args) == 1 and isinstance(args[0], str):
            name = args[0]
            request = kwargs.pop("request", None)
            context = kwargs.pop("context", {})
            if request is None and isinstance(context, dict):
                request = context.get("request")
            return super().TemplateResponse(request=request, name=name, context=context, **kwargs)

        return super().TemplateResponse(*args, **kwargs)

templates = CompatibleJinja2Templates(directory=str(TEMPLATES_DIR))
