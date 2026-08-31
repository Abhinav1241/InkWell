#!/bin/bash
# Inkwell — Deploy to Cloud Run (single service)
set -euo pipefail

export PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID}"
export REGION="${REGION:-us-central1}"
export BUCKET="${PROJECT_ID}-inkwell-assets"
SA="inkwell-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Deploying Inkwell ==="

# Build frontend first (if package.json exists)
if [ -f "frontend/package.json" ]; then
    echo "--- Building frontend ---"
    cd frontend && npm install && npm run build && cd ..
fi

echo "--- Deploying to Cloud Run (single service) ---"
gcloud run deploy inkwell \
  --source . \
  --region "$REGION" \
  --service-account "$SA" \
  --set-env-vars "PROJECT_ID=$PROJECT_ID,REGION=$REGION,ASSETS_BUCKET=$BUCKET,JOBS_TOPIC=inkwell-jobs,COST_MODE=DEV" \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600

# Set up Pub/Sub subscription to push to the same service
SERVICE_URL=$(gcloud run services describe inkwell --region "$REGION" --format='value(status.url)')

echo "--- Setting up Pub/Sub subscription ---"
gcloud pubsub subscriptions create inkwell-jobs-sub \
  --topic inkwell-jobs \
  --push-endpoint "${SERVICE_URL}/pubsub/push" \
  --push-auth-service-account "$SA" 2>/dev/null || echo "Subscription already exists"

echo ""
echo "=== Deployed ==="
echo "URL: $SERVICE_URL"
echo "Cost Mode: DEV (flip to FINAL only for demo recording)"
echo ""
echo "To switch to FINAL mode for the demo:"
echo "  gcloud run services update inkwell --region $REGION --update-env-vars COST_MODE=FINAL"
echo "Switch back immediately after:"
echo "  gcloud run services update inkwell --region $REGION --update-env-vars COST_MODE=DEV"
