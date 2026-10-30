"""Login e logout da interface web (grava/apaga o cookie de sessão)."""

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse

from core import SESSION_COOKIE, config, templates, users
from util.security import create_token, verify_password

router = APIRouter(prefix="/app", tags=["interface web"])

# Tempo de vida do cookie, igual ao do token (ver util/security.py TOKEN_HOURS).
COOKIE_MAX_AGE = 8 * 60 * 60


@router.get("/login")
def login_form(request: Request, next: str = "/app") -> RedirectResponse:
    return templates.TemplateResponse(request, "login.html", {"next": next})


@router.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form("/app")):
    error = "E-mail ou senha inválidos."
    success, user = users.find_by_email(email.lower())

    if not success or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(request, "login.html", {"erro": error, "email": email, "next": next}, status_code=status.HTTP_401_UNAUTHORIZED)

    if user["status"] != "active":
        return templates.TemplateResponse(request, "login.html", {"erro": "Usuário desativado.", "email": email, "next": next}, status_code=status.HTTP_403_FORBIDDEN)

    token = create_token(user["id"], user["role"], config.JWT_SECRET)

    response = RedirectResponse(next or "/app", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(SESSION_COOKIE, token, max_age=COOKIE_MAX_AGE, httponly=True, samesite="lax")
    return response


@router.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse("/app/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response
