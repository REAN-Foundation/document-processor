FROM python:3.10
WORKDIR /app
RUN python -m venv venv
RUN . venv/bin/activate
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 ghostscript -y

COPY requirement.txt /app/
RUN pip install --no-cache-dir -r requirement.txt
COPY . /app
EXPOSE 3000
CMD ["python", "main.py"]