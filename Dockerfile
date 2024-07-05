# Use the official Python image as a base image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV OPENAI_API_KEY None # Get this fro OpenAI

# Create and set the working directory
ADD . /app
WORKDIR /app

# Copy requirements.txt file
COPY requirements.txt .

# Install dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libportaudio2 libasound2 libespeak1 && \
    pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI is running on
EXPOSE 8000

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]