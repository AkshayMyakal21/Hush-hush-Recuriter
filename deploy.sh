set -e
echo "---------------------------------------"
echo "Starting Automated Deployment (CD)"
echo "---------------------------------------"
echo "Pulling latest code..."
git pull origin main
if [ ! -f .env ]; then
    echo "Warning: .env file not found! Copying from .env.example..."
    cp .env.example .env
fi
touch hushhush.db model.joblib
echo "Rebuilding Docker image and launching container"
docker compose up -d --build

echo "Deployment completed successfully!"
echo "Dashboard active at: http://localhost:8501"
