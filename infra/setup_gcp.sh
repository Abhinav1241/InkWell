#!/bin/bash
# Inkwell — GCP Setup Script
# Run once to configure APIs, Firestore, GCS, Pub/Sub, IAM, and budget alert.
set -euo pipefail

export PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID}"
export REGION="${REGION:-us-central1}"
export BUCKET="${PROJECT_ID}-inkwell-assets"

echo "=== Inkwell GCP Setup ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Bucket:  $BUCKET"

gcloud config set project "$PROJECT_ID"

echo "--- Enabling APIs ---"
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  texttospeech.googleapis.com \
  speech.googleapis.com \
  cloudbuild.googleapis.com \
  cloudtrace.googleapis.com \
  billingbudgets.googleapis.com

echo "--- Creating Firestore database ---"
gcloud firestore databases create --location="$REGION" 2>/dev/null || echo "Firestore already exists"

echo "--- Creating GCS bucket ---"
gcloud storage buckets create "gs://$BUCKET" --location="$REGION" 2>/dev/null || echo "Bucket already exists"

echo "--- Creating Pub/Sub topic ---"
gcloud pubsub topics create inkwell-jobs 2>/dev/null || echo "Topic already exists"

echo "--- Creating service account ---"
gcloud iam service-accounts create inkwell-sa 2>/dev/null || echo "SA already exists"
SA="inkwell-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "--- Binding IAM roles ---"
for ROLE in \
  roles/aiplatform.user \
  roles/datastore.user \
  roles/storage.objectAdmin \
  roles/pubsub.editor \
  roles/cloudtrace.agent \
  roles/run.invoker; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA}" --role="$ROLE" \
    --condition=None --quiet
done

echo ""
echo "=== Setup complete ==="
echo ""
echo "⚠️  BUDGET ALERT — Set this up NOW!"
echo "Go to: Console → Billing → Budgets & alerts"
echo "Create a budget for \$25 USD with alerts at 50%, 90%, 100%."
echo ""
echo "Or use gcloud (replace BILLING_ACCOUNT_ID):"
echo "  gcloud billing budgets create --billing-account=BILLING_ACCOUNT_ID \\"
echo "    --display-name='Inkwell budget' --budget-amount=25USD \\"
echo "    --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0"
echo ""
echo "Next: cp .env.example .env && fill values, then run the app."
