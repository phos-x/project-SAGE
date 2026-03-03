import json
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ['MODEL_BUCKET'] = 'mock-test-bucket'
os.environ['MODEL_KEY'] = 'mock-model.joblib'

import app

@pytest.fixture
def mock_cloud_dependencies():
    """
    A pytest fixture that intercepts calls to AWS (boto3) and the file system (joblib).
    This ensures our unit tests run locally, instantly, and for free.
    """
    app.inference_service._model = None
    
    with patch('app.boto3.client') as mock_boto, \
         patch('app.joblib.load') as mock_joblib, \
         patch('app.os.path.exists') as mock_exists:
         
        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = [1] 
        mock_joblib.return_value = mock_model_instance
        
        mock_s3_instance = MagicMock()
        mock_boto.return_value = mock_s3_instance
        
        mock_exists.return_value = False 
        
        yield {
            'joblib': mock_joblib,
            's3': mock_s3_instance,
            'model': mock_model_instance
        }



def test_successful_inference_cold_start(mock_cloud_dependencies):
    """Tests the 'Happy Path' where a valid request triggers a successful prediction."""
    event = {
        'body': json.dumps({'features': [1.5, 2.5, 3.0]})
    }
    
    response = app.lambda_handler(event, context=None)
    
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    assert body['prediction'] == [1]
    assert body['status'] == 'success'
    
    mock_cloud_dependencies['s3'].download_file.assert_called_once_with(
        'mock-test-bucket', 'mock-model.joblib', '/tmp/mock-model.joblib'
    )

def test_validation_missing_body():
    """Tests that the API gracefully handles an entirely empty request."""
    response = app.lambda_handler({}, context=None)
    
    assert response['statusCode'] == 400
    assert 'Request body is missing' in json.loads(response['body'])['error']

def test_validation_invalid_feature_types(mock_cloud_dependencies):
    """Tests the Fail-Fast logic: users sending strings instead of numbers."""
    event = {
        'body': json.dumps({'features': [1.5, "two", 3.0]}) 
    }
    
    response = app.lambda_handler(event, context=None)
    
    assert response['statusCode'] == 400
    assert 'must be numbers' in json.loads(response['body'])['error']
    
    mock_cloud_dependencies['model'].predict.assert_not_called()

@patch('app.logger')
def test_internal_server_error_handling(mock_logger, mock_cloud_dependencies):
    """Tests that unhandled exceptions inside the model don't crash the API gateway."""
    
    mock_cloud_dependencies['model'].predict.side_effect = Exception("Out of memory!")
    
    event = {
        'body': json.dumps({'features': [1.0, 2.0, 3.0]})
    }
    
    response = app.lambda_handler(event, context=None)
    
    assert response['statusCode'] == 500
    assert 'Internal server error' in json.loads(response['body'])['error']
    mock_logger.exception.assert_called_once()