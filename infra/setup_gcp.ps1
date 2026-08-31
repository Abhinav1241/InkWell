# Inkwell — GCP Setup Script (PowerShell)
# Run once to configure APIs, Firestore, GCS, Pub/Sub, IAM, and budget alert.

$ErrorActionPreference = "Stop"

if (-not $env:PROJECT_ID) {
    if (Test-Path ".env") {
        Get-Content .env | ForEach-Object {
            if ($_ -match '^\s*([^#=]+)\s*=\s*(.*)$') {
                [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
            }
        }
    }
}

if (-not $env:PROJECT_ID) {
    Write-Error "Set PROJECT_ID environment variable or define it in .env"
    exit 1
}

$PROJECT_ID = $env:PROJECT_ID
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$BUCKET = if ($env:ASSETS_BUCKET) { $env:ASSETS_BUCKET } else { "${PROJECT_ID}-inkwell-assets" }

Write-Host "=== Inkwell GCP Setup ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region:  $REGION"
Write-Host "Bucket:  $BUCKET"

gcloud config set project $PROJECT_ID

Write-Host "--- Enabling APIs ---" -ForegroundColor Yellow
gcloud services enable `
  run.googleapis.com `
  aiplatform.googleapis.com `
  firestore.googleapis.com `
  storage.googleapis.com `
  pubsub.googleapis.com `
  texttospeech.googleapis.com `
  speech.googleapis.com `
  cloudbuild.googleapis.com `
  cloudtrace.googleapis.com `
  billingbudgets.googleapis.com

Write-Host "--- Creating Firestore database ---" -ForegroundColor Yellow
try { gcloud firestore databases create --location=$REGION } catch { Write-Host "Firestore already exists" }

Write-Host "--- Creating GCS bucket ---" -ForegroundColor Yellow
try { gcloud storage buckets create "gs://$BUCKET" --location=$REGION } catch { Write-Host "Bucket already exists" }

Write-Host "--- Creating Pub/Sub topic ---" -ForegroundColor Yellow
try { gcloud pubsub topics create inkwell-jobs } catch { Write-Host "Topic already exists" }

Write-Host "--- Creating service account ---" -ForegroundColor Yellow
try { gcloud iam service-accounts create inkwell-sa } catch { Write-Host "SA already exists" }
$SA = "inkwell-sa@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "--- Binding IAM roles ---" -ForegroundColor Yellow
$roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/storage.objectAdmin",
    "roles/pubsub.editor",
    "roles/cloudtrace.agent",
    "roles/run.invoker"
)

foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:${SA}" --role=$role `
        --condition=None --quiet
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "WARNING: Set up a budget alert NOW!" -ForegroundColor Red
Write-Host "Go to: Console -> Billing -> Budgets & alerts"
Write-Host "Create a budget for `$25 USD with alerts at 50%, 90%, 100%."
Write-Host ""
Write-Host "Next: Copy .env.example to .env, fill values, then run the app."
