FROM python:3.9

WORKDIR /app

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

# Expose the port FastAPI/healthcheck will run on
EXPOSE 8080

# Run the main app (as list form - safer with arguments)
CMD ["python3", "main.py"]
