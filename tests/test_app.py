import json
import os
import sys
from typing import Any, Dict
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../modules/ml_workspace')))

MOCK_BUCKET = 'mock-test-bucket'
MOCK_KEY = 'mock-model.joblib'
MOCK_LOCAL_PATH = f'/tmp/{MOCK_KEY}'
MOCK_PREDICTION = [1]

os.environ['MODEL_BUCKET'] = MOCK_BUCKET
os.environ['MODEL_KEY'] = MOCK_KEY

import app

@pytest.fixture
def mock_cloud_dependencies() -> Dict[str, MagicMock]:
    """
    A pytest fixture that intercepts calls to AWS and the file system.
    Ensures complete isolation of business logic from cloud infrastructure.
    """
    app.inference_service._model = None
    
    with patch('app.boto3.client') as mock_boto, \
         patch('app.joblib.load') as mock_joblib, \
         patch('app.os.path.exists') as mock_exists:
         
        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value.tolist.return_value = MOCK_PREDICTION 
        mock_joblib.return_value = mock_model_instance
        
        app.inference_service._s3_client = None
        
        mock_s3_instance = MagicMock()
        mock_boto.return_value = mock_s3_instance
        
        mock_exists.return_value = False 
        
        yield {
            'joblib': mock_joblib,
            's3': mock_s3_instance,
            'model': mock_model_instance,
            'exists': mock_exists
        }


def test_successful_inference_cold_start(mock_cloud_dependencies: Dict[str, MagicMock]):
    """Tests an initial valid request, verifying the S3 network call is made."""
    event = {'body': json.dumps({'features': [1.5, 2.5, 3.0]})}
    
    response = app.lambda_handler(event, context=None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['prediction'] == MOCK_PREDICTION
    assert body['status'] == 'success'
    
    mock_cloud_dependencies['s3'].download_file.assert_called_once_with(
        MOCK_BUCKET, MOCK_KEY, MOCK_LOCAL_PATH
    )

def test_successful_inference_warm_start(mock_cloud_dependencies: Dict[str, MagicMock]):
    """Tests the O(1) disk cache optimization. Verifies S3 is NOT called if file exists."""
    mock_cloud_dependencies['exists'].return_value = True
    
    event = {'body': json.dumps({'features': [1.5, 2.5, 3.0]})}
    app.lambda_handler(event, context=None)
    
    mock_cloud_dependencies['s3'].download_file.assert_not_called()


@pytest.mark.parametrize("event_payload, expected_error_fragment", [
    ({}, "Request body is missing"),
    ({'body': 'not-a-json-string'}, "Malformed JSON"),
    ({'body': json.dumps({})}, 'Invalid or missing "features"'),
    ({'body': json.dumps({'features': []})}, 'Invalid or missing "features"'),
    ({'body': json.dumps({'features': [1.5, "malicious_string", 3.0]})}, "must be numbers")
])
def test_input_validation_failures(
    event_payload: Dict[str, Any], 
    expected_error_fragment: str, 
    mock_cloud_dependencies: Dict[str, MagicMock]
):
    """
    Parametrized testing to check all O(N) validation failure modes.
    Ensures bad data is rejected securely before hitting the model layer.
    """
    response = app.lambda_handler(event_payload, context=None)
    
    assert response['statusCode'] == 400
    assert expected_error_fragment in json.loads(response['body'])['error']
    
    mock_cloud_dependencies['model'].predict.assert_not_called()

@patch('app.logger')
def test_internal_server_error_handling(mock_logger: MagicMock, mock_cloud_dependencies: Dict[str, MagicMock]):
    """Tests that unhandled internal exceptions don't leak stack traces to the user."""
    
    mock_cloud_dependencies['model'].predict.side_effect = Exception("Internal Out of Memory Error!")
    
    event = {'body': json.dumps({'features': [1.0, 2.0, 3.0]})}
    response = app.lambda_handler(event, context=None)
    
    assert response['statusCode'] == 500
    assert 'Internal server error' in json.loads(response['body'])['error']
    
    mock_logger.exception.assert_called_once()