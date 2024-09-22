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
                    await handler(scope, params, receive, send)
                else:
                    await self.not_found(send)
            else:
                await self.not_found(send)

        except Exception as e:
            await self.internal_server_error(send, str(e))

    async def factorial(self, scope: Dict[str, Any], params: Dict[str, Any], receive: Callable, send: Callable) -> None:
        try:
            n_str = params.get("n", [None])[0]
            if n_str is None:
                await self.unprocessable_entity(send)
                return

            try:
                n = int(n_str)
            except ValueError:
                await self.unprocessable_entity(send)
                return

            if n < 0:
                await self.bad_request(send)
                return
            factorial_result = calculate_factorial(n)
            response_body = {"result": factorial_result}
            await self.send_response(send, response_body)
        except Exception:
            await self.internal_server_error(send)

    async def fibonacci(self, scope: Dict[str, Any], params: Dict[str, Any], receive: Callable, send: Callable) -> None:
        try:
            path = scope["path"]
            n_str = path.split("/fibonacci/")[-1]

            try:
                n = int(n_str)
            except ValueError:
                await self.unprocessable_entity(send)
                return

            if n < 0:
                await self.bad_request(send)
                return

            fibonacci_result = calculate_fibonacci(n)
            response_body = {"result": fibonacci_result}
            await self.send_response(send, response_body)
        except Exception:
            await self.internal_server_error(send)

    async def mean(self, scope: Dict[str, Any], params: Dict[str, Any], receive: Callable, send: Callable) -> None:
        try:
            body = await self.get_request_body(receive)

            if not isinstance(body, list):
                await self.unprocessable_entity(send)
                return

            if len(body) == 0:
                await self.bad_request(send)
                return

            if not all(isinstance(num, (float, int)) for num in body):
                await self.unprocessable_entity(send)
                return

            mean_result = calculate_mean(body)
            response_body = {"result": mean_result}
            await self.send_response(send, response_body)

        except ValueError:
            await self.unprocessable_entity(send)
        except Exception as e:
            await self.internal_server_error(send, str(e))

    async def get_request_body(self, receive: Callable) -> Any:
        """Helper function to extract and parse JSON body from request."""
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        if body:
            return json.loads(body)
        return None

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
