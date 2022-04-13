FROM python:3.8.10
COPY mosaic_generator.py /app
COPY docker_code.py /app
WORKDIR /app
RUN pip install opencv-python-headless
CMD ["python","codigo.py"]
