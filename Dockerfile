# Using latest python as base
FROM python:latest

# Set the workdir 
WORKDIR /app

# Copying all files to image
COPY ./ .


# Install the required dependancies
RUN pip install -r requirements.txt

# Start the container
CMD ["flask", "run"]
