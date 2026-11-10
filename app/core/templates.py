from starlette.templating import Jinja2Templates as StarletteJinja2Templates

class Jinja2Templates(StarletteJinja2Templates):
    """
    Subclasse de Jinja2Templates compatível com versões antigas e novas do Starlette:
      - Chamada clássica: TemplateResponse("login.html", {"request": request, ...})
      - Chamada moderna: TemplateResponse(request, "login.html", {...})
      - Chamada por kwargs: TemplateResponse(name="login.html", context={"request": request})
    """
    def TemplateResponse(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            name = args[0]
            context = args[1] if len(args) > 1 else kwargs.pop("context", {})
            req = kwargs.pop("request", None)
            if req is None and isinstance(context, dict):
                req = context.get("request")
            return super().TemplateResponse(req, name, context, *args[2:], **kwargs)

        if "name" in kwargs and "request" not in kwargs and len(args) < 1:
            context = kwargs.get("context", {})
            req = context.get("request") if isinstance(context, dict) else None
            return super().TemplateResponse(req, kwargs["name"], context)

        return super().TemplateResponse(*args, **kwargs)

