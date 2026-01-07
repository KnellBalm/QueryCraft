#!/bin/bash
# functions/deploy.sh
# Cloud Functions 배포 스크립트

set -e

PROJECT_ID="${GCP_PROJECT_ID:-querycraft-483512}"
REGION="us-central1"

echo "🚀 Deploying Cloud Functions to $PROJECT_ID"

# Problem Worker 배포
echo "📝 Deploying problem_worker..."
gcloud functions deploy problem-worker \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=./problem_worker \
    --entry-point=generate_problems \
    --trigger-http \
    --allow-unauthenticated \
    --memory=512Mi \
    --timeout=540s \
    --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Tip Worker 배포
echo "💡 Deploying tip_worker..."
gcloud functions deploy tip-worker \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=./tip_worker \
    --entry-point=generate_tip \
    --trigger-http \
    --allow-unauthenticated \
    --memory=256Mi \
    --timeout=60s \
    --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

echo "✅ Deployment complete!"

# Cloud Scheduler 설정
echo "⏰ Setting up Cloud Scheduler..."

# 문제 생성 스케줄러 (KST 01:00 = UTC 16:00 전날)
gcloud scheduler jobs create http problem-generation-job \
    --location=$REGION \
    --schedule="0 16 * * 0-4" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/problem-worker" \
    --http-method=POST \
    --time-zone="UTC" \
    --description="Daily problem generation (Mon-Fri KST 01:00)" \
    || echo "Job already exists, updating..."

# 팁 생성 스케줄러 (KST 00:30)
gcloud scheduler jobs create http tip-generation-job \
    --location=$REGION \
    --schedule="30 15 * * *" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/tip-worker" \
    --http-method=POST \
    --time-zone="UTC" \
    --description="Daily tip generation (KST 00:30)" \
    || echo "Job already exists, updating..."

echo "🎉 All done! Functions and schedulers are ready."
