# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install tesseract-ocr and other dependencies
RUN apt-get update && apt-get install -y tesseract-ocr

# Copy the current directory contents into the container at /app
COPY . /app

# Create the uploads directory
RUN mkdir /app/uploads

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]