# Inkwell — Deploy to Cloud Run (PowerShell)

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
    Write-Error "Set PROJECT_ID environment variable first"
    exit 1
}

$PROJECT_ID = $env:PROJECT_ID
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$BUCKET = "${PROJECT_ID}-inkwell-assets"
$SA = "inkwell-sa@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "=== Deploying Inkwell ===" -ForegroundColor Cyan

# Build frontend if exists
if (Test-Path "frontend/package.json") {
    Write-Host "--- Building frontend ---" -ForegroundColor Yellow
    Push-Location frontend
    npm install
    npm run build
    Pop-Location
}

Write-Host "--- Deploying to Cloud Run (single service) ---" -ForegroundColor Yellow
gcloud run deploy inkwell `
  --source . `
  --region $REGION `
  --service-account $SA `
  --set-env-vars "PROJECT_ID=$PROJECT_ID,REGION=$REGION,ASSETS_BUCKET=$BUCKET,JOBS_TOPIC=inkwell-jobs,COST_MODE=DEV" `
  --allow-unauthenticated `
  --memory 4Gi `
  --cpu 2 `
  --timeout 3600 `
  --quiet

$SERVICE_URL = gcloud run services describe inkwell --region $REGION --format='value(status.url)'

Write-Host "--- Setting up Pub/Sub subscription ---" -ForegroundColor Yellow
try {
    gcloud pubsub subscriptions create inkwell-jobs-sub `
      --topic inkwell-jobs `
      --push-endpoint "${SERVICE_URL}/pubsub/push" `
      --push-auth-service-account $SA
} catch { Write-Host "Subscription already exists" }

Write-Host ""
Write-Host "=== Deployed ===" -ForegroundColor Green
Write-Host "URL: $SERVICE_URL"
Write-Host "Cost Mode: DEV (flip to FINAL only for demo recording)"
Write-Host ""
Write-Host "To switch to FINAL mode for the demo:"
Write-Host "  gcloud run services update inkwell --region $REGION --update-env-vars COST_MODE=FINAL"
