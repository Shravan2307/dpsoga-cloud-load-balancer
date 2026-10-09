from fastapi import APIRouter, HTTPException
from app.schemas.api import PredictionTrainRequest, PredictionRequest, GenericResult, PredictionResponse
from app.services.prediction import train_prediction, predict_values

router = APIRouter(prefix='/api/prediction', tags=['prediction'])

@router.post('/train', response_model=GenericResult, summary='Train the PSO-GA optimized CNN-LSTM')
def train(req: PredictionTrainRequest):
    return {'status': 'trained', 'result': train_prediction(req)}

@router.post('/predict', response_model=PredictionResponse, summary='Predict the next resource-utilization vector')
def predict(req: PredictionRequest):
    try:
        return predict_values(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
