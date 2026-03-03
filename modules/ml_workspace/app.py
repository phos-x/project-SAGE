import json
import logging
import os
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError
import joblib

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class InferenceService:
    """Encapsulates model loading and inference logic using Lazy Initialization."""
    
    def __init__(self):
        self._model = None
        self._s3_client = None  
        
        self.bucket_name = os.environ.get('MODEL_BUCKET')
        self.model_key = os.environ.get('MODEL_KEY', 'model.joblib')
        self.local_path = f'/tmp/{self.model_key}'

    @property
    def s3_client(self):
        """Lazy initialization of the Boto3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3')
        return self._s3_client

    def _load_model(self) -> None:
        """Downloads and loads the model into memory. Executes only on cold starts."""
        if self._model is not None:
            return

        if not self.bucket_name:
            raise ValueError("MODEL_BUCKET environment variable is strictly required.")

        try:
            if not os.path.exists(self.local_path):
                logger.info(f"Downloading {self.model_key} from s3://{self.bucket_name}...")
                self.s3_client.download_file(self.bucket_name, self.model_key, self.local_path)
            else:
                logger.info(f"Model file already exists locally at {self.local_path}.")

            logger.info("Loading model into memory...")
            self._model = joblib.load(self.local_path)
            logger.info("Model loaded successfully.")
            
        except ClientError as e:
            logger.error(f"S3 Download Error: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise

    def predict(self, features: List[float]) -> List[Any]:
        """Performs inference using the loaded model."""
        self._load_model()
        return self._model.predict([features]).tolist()

inference_service = InferenceService()

def create_response(status_code: int, body_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to keep API Gateway responses DRY (Don't Repeat Yourself)."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body_dict)
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main AWS Lambda entry point."""
    try:
        body_str = event.get('body')
        if not body_str:
            return create_response(400, {'error': 'Request body is missing.'})
            
        body = json.loads(body_str)
        features = body.get('features')
        
        if not features or not isinstance(features, list):
            return create_response(400, {'error': 'Invalid or missing "features". Must be a non-empty list.'})
            
        if not all(isinstance(x, (int, float)) for x in features):
            return create_response(400, {'error': 'All elements in the "features" array must be numbers.'})

        prediction = inference_service.predict(features)
        
        return create_response(200, {
            'prediction': prediction,
            'status': 'success'
        })
        
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON body.")
        return create_response(400, {'error': 'Malformed JSON in request body.'})
    except ValueError as ve:
        logger.error(f"Validation Error: {str(ve)}")
        return create_response(400, {'error': str(ve)})
    except Exception as e:
        logger.exception("Unexpected internal server error during prediction.")
        return create_response(500, {'error': 'Internal server error.'})