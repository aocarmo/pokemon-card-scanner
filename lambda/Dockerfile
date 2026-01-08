FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model and code
COPY model/current/ ${LAMBDA_TASK_ROOT}/model/
COPY *.py ${LAMBDA_TASK_ROOT}/

# Set handler
CMD ["handler.lambda_handler"]
