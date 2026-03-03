FROM public.ecr.aws/lambda/python:3.9

RUN pip install scikit-learn joblib numpy boto3

COPY app.py ${LAMBDA_TASK_ROOT}

CMD [ "app.lambda_handler" ]