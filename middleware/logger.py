from fastapi import Request
import json

async def logger_middleware(request: Request, call_next):
    print(f"[{request.method}] {request.url}")
    if request.method == "POST":
        try:
            body = await request.body()
            if body:
                body_json = json.loads(body)
                if "password" in body_json:
                    body_json["password"] = "********"
                print(f"Body: {body_json}")
        except Exception:
            pass
    response = await call_next(request)
    return response
