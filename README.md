# itmo_backend_python

This project implements a simple ASGI application with `uvicorn` that includes basic routing and error handling.

## Features:
- Handles GET requests for:
  - `/factorial`
  - `/fibonacci`
  - `/mean`
- Provides standard error handling for common HTTP errors:
  - 400 Bad Request
  - 404 Not Found
  - 405 Method Not Allowed
  - 500 Internal Server Error

## Run

To run the application using Docker, simply use the following command:

```bash
make run
