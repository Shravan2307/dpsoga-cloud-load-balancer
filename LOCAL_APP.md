# Local application layer

The research implementation under `src/` remains the source of truth for optimization, simulation, data processing, and CNN-LSTM behavior. The new `app/` package is only an API/service adapter and does not duplicate those algorithms.

## FastAPI

Start the backend locally:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Backend health check |
| POST | `/api/experiments/run` | Run a configured experiment |
| POST | `/api/optimization/ga` | Run GA through the existing simulator |
| POST | `/api/optimization/pso` | Run PSO through the existing simulator |
| POST | `/api/optimization/psoga` | Run hybrid PSO-GA through the existing simulator |
| POST | `/api/prediction/train` | Train the existing PSO-GA optimized CNN-LSTM |
| POST | `/api/prediction/predict` | Predict with the in-memory trained model |
| GET | `/api/results/phase1` | Read the generated Phase 1 table |
| GET | `/api/results/phase2` | Read the generated Phase 2 result |

Swagger/OpenAPI is available at `http://localhost:8000/docs`.

Example request:

```bash
curl -X POST http://localhost:8000/api/optimization/psoga \
  -H 'Content-Type: application/json' \
  -d '{"tasks":50,"vms":12,"seed":42,"population_size":24,"iterations":20}'
```

The response uses the current research implementation’s metric semantics. In particular, the existing `makespan` field remains the current implementation’s composite fitness value; this behavior was intentionally not changed while adding the application layer.

## Docker Compose

Create the local environment file once:

```bash
cp .env.example .env
docker compose up --build
```

The backend is available at `http://localhost:8000`, Swagger at `http://localhost:8000/docs`, and the API-backed dashboard at `http://localhost:8501`.

The dashboard calls FastAPI. It does not import or duplicate the research optimizer/simulator logic.

## Local-first and future AWS path

The application requires no AWS credentials, cloud GPU, external database, OpenAI API, Anthropic API, or paid API. Synthetic data remains available. Local datasets can be supplied through `DATASET_PATH` or an explicit request path.

AWS is intentionally not deployed or required. A future deployment path is:

```text
Docker → Amazon ECR → AWS ECS → FastAPI
```

An optional future data path could use S3 for the Google workload dataset, but local filesystem ingestion remains the default and supported path.
