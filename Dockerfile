# Use official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /

# Copy project files
# COPY . /

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Command to run the app
ENTRYPOINT ["python", "path_planner.py"]
