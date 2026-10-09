from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.loader import load_dataset
from src.data.preprocessing import normalize, make_sequences, split
from src.models.cnn_lstm import CNNLSTM, train_model, predict
from src.models.psoga_optimizer import CNNLSTMPSOGA

_models: dict[str, tuple[object, int]] = {}
_latest = 'latest'


def train_prediction(req):
    df = load_dataset(req.dataset, req.google_path, n=240, seed=req.seed)
    values, scaler = normalize(df)
    X, y = make_sequences(values, req.window)
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = split(X, y)
    optimizer = CNNLSTMPSOGA(
        x_train, y_train, x_val, y_val,
        seed=req.seed,
        population_size=req.optimizer_population,
        iterations=req.optimizer_iterations,
    )
    params, validation_mae, history = optimizer.run()
    architecture = {k: params[k] for k in ['filters', 'kernel_size', 'pool_size', 'hidden_units', 'layers', 'dropout']}
    model = CNNLSTM(X.shape[2], **architecture, output_size=y.shape[1])
    train_model(
        model,
        np.concatenate([x_train, x_val]),
        np.concatenate([y_train, y_val]),
        epochs=req.epochs,
        lr=params['learning_rate'],
        batch_size=params['batch_size'],
        seed=req.seed,
    )
    _models[_latest] = (model, X.shape[2])
    return {
        'model_id': _latest,
        'dataset': req.dataset,
        'feature_count': int(X.shape[2]),
        'validation_mae': float(validation_mae),
        'optimized_parameters': params,
        'optimizer_history': history,
        'test_samples': int(len(x_test)),
        'scaler': scaler,
    }


def predict_values(req):
    if req.model_id not in _models:
        raise ValueError('Model is not trained. Call POST /api/prediction/train first.')
    model, feature_count = _models[req.model_id]
    arr = np.asarray(req.values, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] != feature_count:
        raise ValueError(f'values must have shape [time, {feature_count}]')
    prediction = predict(model, arr[None, :, :])[0]
    return {'model_id': req.model_id, 'prediction': prediction.tolist(), 'feature_count': feature_count}
