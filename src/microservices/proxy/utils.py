from fastapi import Response
import httpx

def make_response(resp: httpx.Response) -> Response:
    return Response(
        content = resp.content,
        status_code = resp.status_code,
        headers = dict(resp.headers)
    )