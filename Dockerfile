FROM python:3.10-slim

# Set the working directory directly in the container
WORKDIR /app

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0
ENV SECRET_KEY=build-only-placeholder-key-replace-in-render
ENV ALLOWED_HOSTS=.onrender.com,localhost

# Install the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY . .

# Prepare static files and run database migrations
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

# Expose the port exactly as Render expects
EXPOSE 8000

# Tell Docker to boot our Gunicorn server, binding to all interfaces
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
