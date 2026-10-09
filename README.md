# DPSO-GA Intelligent Cloud Resource Optimization and Auto-Scaling System Using CNN-LSTM

This project incrementally extends the existing DPSO-GA research prototype into a local-first cloud resource optimization demo platform. The original GA, PSO, hybrid PSO-GA, simulation, migration, resource classification, CNN-LSTM, Phase 1, Phase 2, FastAPI, dashboard, and tests are preserved.

## Project objective

```text
Workload / CSV / profile
        ↓
Automatic workload analysis
        ↓
CNN-LSTM workload prediction
        ↓
GA vs PSO vs PSO-GA on the same objective
        ↓
Actual best-result selection
        ↓
ResourceDecisionEngine
        ↓
SimulationAdapter OR AWSCloudAdapter
        ↓
Cloud metrics / feedback
```

The default execution mode is simulation. AWS support is optional, credential-free in dry-run mode, and separated from the research algorithms.

## Architecture

The implementation diagram is in [`docs/architecture.mmd`](docs/architecture.mmd). The main application layers are:

- `src/optimization`: GA, PSO, hybrid PSO-GA, population, and fitness.
- `src/simulation`: CloudSim-style entities, host placement, scheduling, and migration.
- `src/data` and `src/workload`: research trace support plus automatic CSV/profile ingestion and analysis.
- `src/models`: CNN-LSTM and PSO-GA hyperparameter search.
- `src/decision_engine.py`: provider-independent capacity decision logic.
- `app/services/automation.py`: workload → prediction → comparison → decision orchestration.
- `app/services/cloud.py`: simulation, optional ECS/S3/CloudWatch adapters.
- `app/`: FastAPI routes and Pydantic models.
- `dashboard/app.py`: Streamlit client of the FastAPI backend.

## Installation

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

AWS is not required for local work. Install its optional SDK only when AWS mode is needed:

```bash
pip install -r requirements-aws.txt
```

## Local API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

Important endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend health |
| POST | `/api/workload/upload` | Upload and validate a CSV |
| POST | `/api/workload/analyze` | Analyze a profile or local CSV |
| POST | `/api/workload/predict` | Train/predict automatically after ingestion |
| POST | `/api/workload/pipeline` | Run the complete local pipeline |
| POST | `/api/optimize` | Compare GA, PSO, and PSO-GA fairly |
| GET | `/api/optimization/results` | Read latest comparison |
| POST | `/api/decisions` | Generate capacity decision |
| GET | `/api/decisions` | Read latest decision |
| GET | `/api/cloud/status` | Simulation or AWS status |
| GET | `/api/cloud/metrics` | Local/AWS metric status |
| POST | `/api/cloud/scale` | Simulated or AWS dry-run scaling |
| GET | `/api/results/phase1` | Existing Phase 1 table |
| GET | `/api/results/phase2` | Existing Phase 2 result |

Example complete pipeline:

```bash
curl -X POST http://localhost:8000/api/workload/pipeline \
  -H 'Content-Type: application/json' \
  -d '{"source":"Banking","tasks":6,"vms":3,"seed":7,"dry_run":true}'
```

The result contains workload statistics, prediction MAE/RMSE, all three optimizer results, the actual winner by fitness, and a capacity decision.

## Dashboard

Start the API first, then in another terminal:

```bash
DASHBOARD_API_URL=http://localhost:8000 streamlit run dashboard/app.py --server.port 8501
```

Open `http://localhost:8501`.

The dashboard supports:

1. Workload profile selection or CSV upload.
2. Automatic workload analysis and classification.
3. CNN-LSTM prediction and actual-vs-predicted chart.
4. GA/PSO/PSO-GA comparison on the same workload.
5. Actual winner highlighting.
6. Resource recommendation and SCALE OUT/SCALE IN/MAINTAIN decision.
7. Simulation mode and AWS dry-run mode.
8. Existing Phase 1 and Phase 2 result tables.

## Workload input

Predefined profiles:

- E-commerce
- Banking
- Streaming
- Education
- Healthcare
- SaaS
- Custom CSV

CSV columns are detected using aliases. The preferred fields are:

```text
timestamp,cpu,memory,network,requests,latency
```

Only one recognized numeric workload column is required. Missing recognized columns receive safe defaults; missing values are interpolated. CPU, memory, and network values are accepted as fractions or percentages. Timestamp columns are parsed and sorted.

Automatically calculated statistics include:

- Average and peak CPU.
- Average and peak memory.
- Average and peak network.
- Average and peak request rate.
- Average and peak latency.
- Workload intensity.
- Volatility.
- Trend.
- Estimated future demand.
- Overload probability.
- Underutilization probability.
- LOW, MODERATE, HIGH, BURSTY, or OVERLOADED classification.

Thresholds are configurable in the analyzer rather than being hidden in the final result.

## Existing research experiments

These commands preserve the original research workflow:

```bash
python run_experiment.py --phase 1 --seed 42
python run_experiment.py --phase 2 --dataset synthetic --seed 42
python run_experiment.py --all --seed 42
```

Phase 1 remains the CloudSim-style GA, PSO, and genuine hybrid PSO-GA scheduler. Phase 2 remains the CNN-LSTM baseline versus PSO-GA hyperparameter search. Existing numerical behavior was not replaced by fabricated values.

## Google Cluster Trace Benchmark

To evaluate the resource optimization algorithms (GA, PSO, DPSO-GA) on a real-world workload, this system integrates the **Google Cluster Trace (2011/v2)** dataset. 

**Why Google Cluster Trace?**
Because it provides a real-world workload trace that allows the proposed resource optimization algorithms to be evaluated under realistic workload patterns rather than only synthetic workloads. This adds significant research validity to the comparison.

**Benchmark Methodology:**
1. **Source Dataset**: Google Cluster Data 2011-2 `task_usage` table (https://github.com/google/cluster-data).
2. **Preprocessing**: The raw microsecond-level task usage data is aggregated into configurable time windows (e.g., 60 seconds).
3. **Data Type**: Network and Latency metrics are explicitly derived from CPU and Task events defensively as they are not natively present in the Google Trace task usage table.
4. **Execution**: The benchmark runner loads the trace, generates tasks chronologically matching the trace workload demand, and executes the GA, PSO, and DPSO-GA algorithms.
5. **Metrics**: Real-time VM allocation count, CPU/Memory utilization, derived SLA violations, resource wastage, scaling events, execution time, and estimated cost are calculated.
6. **Reproducibility**: The dataset path, window size, max records, and seed are configurable to ensure reproducible research results.

**How to Run the Benchmark:**
1. Ensure you have the trace CSV. A synthetic sample is provided at `data/raw/google_cluster_trace/sample_task_usage.csv`. To benchmark real data, download the 2011-2 `task_usage` dataset and place it in the directory.
2. Open the Streamlit Dashboard.
3. Navigate to **GOOGLE TRACE LAB**.
4. Configure the dataset path, window size, and select the algorithms to compare.
5. Click **RUN BENCHMARK** to generate the comparison table and VM allocation history graphs.

## Docker

Local simulation image:

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8501`

To include the optional AWS SDK in the image, set this in `.env` before building:

```text
INSTALL_AWS=1
```

Then rebuild:

```bash
docker compose build --no-cache
docker compose up
```

## AWS architecture and safety

The selected AWS target is ECS/Fargate. S3 is optional for workload/model/result storage. CloudWatch is used for application metrics/logging when configured. Lambda, SQS, and DynamoDB are intentionally not required because the current pipeline does not need them.

AWS files:

- [`deploy/aws/README.md`](deploy/aws/README.md)
- [`deploy/aws/ecs-task-definition.template.json`](deploy/aws/ecs-task-definition.template.json)
- [`deploy/aws/iam-policy.example.json`](deploy/aws/iam-policy.example.json)

Required AWS variables are documented in `.env.example`:

```text
AWS_REGION
AWS_S3_BUCKET
AWS_ECS_CLUSTER
AWS_ECS_SERVICE
AWS_DRY_RUN
CLOUDWATCH_NAMESPACE
```

AWS credentials are never stored in this repository. Use an ECS task role or local AWS profile/IAM role. `AWS_DRY_RUN=true` is the safe default and does not change infrastructure. Real scaling requires `AWS_DRY_RUN=false`, configured ECS identifiers, reviewed IAM permissions, and explicit operator action.

## Results and reporting

The automated pipeline writes:

```text
results/automation/latest_report.json
results/automation/latest_optimization.csv
```

These are clearly simulation or AWS-mode outputs based on the selected execution mode. No simulated value is presented as an AWS measurement.

## Testing

```bash
pytest -q
```

The test suite covers:

- Existing GA, PSO, hybrid PSO-GA, resource, migration, and model behavior.
- Workload profile generation.
- CSV alias detection and missing-value handling.
- Invalid datasets.
- Workload analysis and classification.
- Resource decision limits.
- Simulation adapter.
- AWS dry-run adapter.
- FastAPI health, optimization, upload validation, workload analysis, and cloud scaling.

AWS tests use dry-run behavior and do not require real AWS infrastructure or credentials.

## Reproducibility

Use explicit seeds. The original Phase 1 and Phase 2 commands remain deterministic for the same environment and seed. New profile generation, workload analysis, prediction, and comparison also accept a seed. Results are generated by the implementation at runtime and are not hardcoded from the paper.

## Security

Never commit:

- AWS access keys.
- Private keys.
- Tokens.
- Passwords.
- Production `.env` files.

`.gitignore` excludes `.env`, credentials, keys, caches, and generated logs.

## Cost control

For a student demonstration:

- Keep ECS desired count at 1.
- Use a small Fargate task.
- Keep AWS dry-run enabled initially.
- Use short experiments and small datasets.
- Avoid NAT gateways and load balancers unless required.
- Delete ECS services, task definitions, ECR images, S3 objects, and CloudWatch log groups after the demonstration.

## Known limitations

- The original research simulator has simplified CloudSim-style behavior and retains its existing metric semantics.
- The current CNN-LSTM automation uses a lightweight local training configuration for demonstration.
- AWS metric queries and alarms need deployment-specific CloudWatch dimensions and are not fabricated locally.
- AWS real scaling is intentionally not exercised without user-supplied infrastructure and credentials.
- Model artifacts are not yet persisted to S3 automatically; the S3 adapter provides the storage primitive.
