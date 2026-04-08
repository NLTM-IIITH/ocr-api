# OCR Website Service

This directory contains the web API and related scripts for running OCR inference. It is built with FastAPI and provides endpoints to process image content using various OCR models.

## Structure

- `main.py` - entrypoint that starts Uvicorn server using `server.app`.
- `server/` - core application code.
  - `app.py` - FastAPI application setup, middleware, request logging, and route handlers.
  - `config.py` - configuration constants (port, image folder, language maps, database info, etc.).
  - `database.py` - MongoDB connection handlers.
  - `dependencies.py` - FastAPI dependencies such as saving uploaded images.
  - `helper.py` - helper functions for invoking OCR backends, loading models, processing outputs, validating parameters.
  - `models.py` - Pydantic models and enums used by the API.
  - `modules/` - subrouters for features like adhoc, external, IITB v2 and others.

- Shell scripts (`infer.sh`, `infer_v0.sh`, etc.) – wrappers that call different versions of OCR inference binaries.
- `tests/` - unit/functional tests for the API.
- `images/` - temporary upload folder.

## Usage

1. Ensure dependencies are installed (`requirements.txt`).
2. Start service with `python main.py` or using Docker (`Dockerfile` provided).
3. API accessible at `/ocr/infer`, `/ocr/test`, etc. Swagger docs at `/ocr/docs`.

### Request Flow

1. Incoming JSON or multipart data is validated by Pydantic models.
2. Images are saved to a temporary directory.
3. Language/version/modality parameters are normalized and verified.
4. Appropriate shell script or helper function is invoked to run OCR backend. Outputs are processed into standardized response objects.
5. Logs are stored in MongoDB; instrumentation is exposed via Prometheus.

## Error Handling

- Model validation (`verify_model`) raises exceptions if unsupported combinations are requested. FastAPI returns 422 or 400 accordingly.
- Helper functions wrap external command execution which returns return codes; non-zero return codes typically raise an error or log.
- Temporary directories are used; cleanup handled by Python's `TemporaryDirectory` context.
- File system operations use `os.system` or `shutil` and may raise `OSError` on failure.
- Database errors propagate through Motor; the app registers startup/shutdown events to manage connections.
- Middleware logs requests; exceptions raised in route handlers are returned as HTTP error responses with stack traces in debug mode.

## Development Notes

- CORS is configured to allow all origins for ease of testing.
- The server uses `prometheus_fastapi_instrumentator` for metrics.
- Scripts support multiple model versions; updating them is necessary when adding new models.

## Testing

- `tests/` contains PyTest suites; run with `pytest`.
- `test.sh` provides a quick smoke test using curl.

## Maintenance

- Keep `requirements.txt` updated and reinstall when packages change.
- Monitor MongoDB connection parameters in `config.py`.
- When adding new languages/versions, update `config.py` mapping dictionaries and ensure the corresponding inference script exists.

> **Note:** This README is auto-generated and summarizes key elements of the codebase. For detailed implementation, refer to individual source files.
