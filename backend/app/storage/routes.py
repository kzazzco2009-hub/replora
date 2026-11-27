"""The local stand-in for signed storage URLs (P6.1). Not part of the API contract.

These routes play the part of Supabase's signed upload and download URLs, so they live outside
the v1 router: the signed, short-lived, single-purpose token is the authorization (S-34, S-36).
"""

from urllib.parse import quote

from fastapi import APIRouter, Request, Response

from app.api.problem import ProblemError
from app.storage.local import ROUTE
from app.storage.signing import verify

router = APIRouter(prefix=ROUTE, tags=["storage"], include_in_schema=False)


def _claims(request: Request, token: str, op: str) -> dict:
    claims = verify(token, request.app.state.storage.signing_key, request.app.state.clock(), op)
    if claims is None:
        raise ProblemError(403, "TOKEN_INVALID", "This link is invalid or has expired")
    return claims


@router.put("/{token}")
async def upload(token: str, request: Request) -> Response:
    claims = _claims(request, token, "put")
    data = await request.body()
    if len(data) > claims["size"]:
        raise ProblemError(413, "FILE_TOO_LARGE", "More bytes than declared")
    request.app.state.storage.put(claims["key"], data)
    return Response(status_code=200)


@router.get("/{token}")
def download(token: str, request: Request) -> Response:
    claims = _claims(request, token, "get")
    disposition = f"attachment; filename*=UTF-8''{quote(claims['name'])}"
    headers = {"Content-Disposition": disposition, "X-Content-Type-Options": "nosniff",
               "Cache-Control": "private, no-store"}  # fmt: skip
    data = request.app.state.storage.open(claims["key"])
    return Response(data, media_type="application/octet-stream", headers=headers)
