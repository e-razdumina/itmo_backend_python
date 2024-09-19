import json
from typing import Any, Callable, Dict
from urllib.parse import parse_qs

from .utils import calculate_factorial, calculate_fibonacci, calculate_mean


class ServerApp:
    def __init__(self) -> None:
        self.routes: Dict[str, Dict[str, Callable]] = {
            "GET": {
                "/factorial": self.factorial,
                "/fibonacci": self.fibonacci,
                "/mean": self.mean,
            }
        }

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        try:
            assert scope["type"] == "http"
            method: str = scope["method"]
            path: str = scope["path"]
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)

            if method in self.routes:
                if path in self.routes[method]:
                    handler = self.routes[method][path]
                    await handler(scope, params, send)
                else:
                    await self.not_found(send)
            else:
                await self.method_not_allowed(send)

        except Exception as e:
            await self.internal_server_error(send, str(e))

    async def factorial(self, scope: Dict[str, Any], params: Dict[str, Any], send: Callable) -> None:
        try:
            n = int(params.get("n", [None])[0])
            if n is None:
                raise ValueError("Missing 'n' parameter")

            factorial_result = calculate_factorial(n)
            response_body = {"factorial": factorial_result}
            await self.send_response(send, response_body)
        except ValueError:
            await self.bad_request(send)
        except Exception:
            await self.internal_server_error(send)

    async def fibonacci(self, scope: Dict[str, Any], params: Dict[str, Any], send: Callable) -> None:
        try:
            n = int(params.get("n", [None])[0])
            if n is None:
                raise ValueError("Missing 'n' parameter")

            fibonacci_result = calculate_fibonacci(n)
            response_body = {"fibonacci": fibonacci_result}
            await self.send_response(send, response_body)
        except ValueError:
            await self.bad_request(send)
        except Exception:
            await self.internal_server_error(send)

    async def mean(self, scope: Dict[str, Any], params: Dict[str, Any], send: Callable) -> None:
        try:
            numbers_str = params.get("numbers", [None])[0]
            if numbers_str is None:
                raise ValueError("Missing 'numbers' parameter")

            numbers = list(map(float, numbers_str.split(',')))
            mean_result = calculate_mean(numbers)
            response_body = {"mean": mean_result}
            await self.send_response(send, response_body)
        except ValueError:
            await self.bad_request(send)
        except Exception:
            await self.internal_server_error(send)

    async def send_response(self, send: Callable, body: Dict[str, Any], status_code: int = 200) -> None:
        body_bytes = json.dumps(body).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body_bytes)).encode("utf-8"))
            ]
        })
        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })

    # 400 Bad Request Handler
    async def bad_request(self, send: Callable) -> None:
        await self.error_response(send, "Bad Request", status_code=400)

    # 422 Unprocessable Entity Handler
    async def unprocessable_entity(self, send: Callable) -> None:
        await self.error_response(send, "Unprocessable Entity", status_code=422)

    # 405 Method Not Allowed Handler
    async def method_not_allowed(self, send: Callable) -> None:
        await self.error_response(send, "Method Not Allowed", status_code=405)

    # 404 Not Found Handler
    async def not_found(self, send: Callable) -> None:
        await self.error_response(send, "Not Found", status_code=404)

    # 500 Internal Server Error Handler
    async def internal_server_error(self, send: Callable, error_msg: str = "Internal Server Error") -> None:
        await self.error_response(send, error_msg, status_code=500)

    # Common method for generating error responses
    async def error_response(self, send: Callable, message: str, status_code: int) -> None:
        response_body = {"error": message}
        await self.send_response(send, response_body, status_code=status_code)
