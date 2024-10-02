FROM python:3.11
WORKDIR /Verba

# Create the data directory (if it doesn't already exist in your project)
RUN mkdir -p /data

# Copy the key file from your local context into the image's /data directory
COPY /home/ec2-user/myverba/goldenverba/components/generation/myupsc-mentor-ded3f62e859b.json /data/

# Set the necessary permissions *inside* the image:
RUN chmod 600 /data/myupsc-mentor-ded3f62e859b.json # or any other required permission


COPY . /Verba  # Copy your application code
RUN pip install -e '.'


# Set the environment variable *inside* the image
ENV GOOGLE_APPLICATION_CREDENTIALS /data/myupsc-mentor-ded3f62e859b.json

EXPOSE 8000
CMD ["verba", "start"]