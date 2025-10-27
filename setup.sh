#!/bin/bash

# Stop on any error
set -e

# --- Color Codes ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Helper Functions ---
function print_info { echo -e "${BLUE}INFO: $1${NC}"; }
function print_success { echo -e "${GREEN}SUCCESS: $1${NC}"; }
function print_error { echo -e "${RED}ERROR: $1${NC}"; exit 1; }
function print_prompt { echo -e -n "${YELLOW}$1${NC}"; }

# --- Check for required tools ---
print_info "Checking for required tools (gcloud, docker, python3, pip)..."
command -v gcloud >/dev/null 2>&1 || print_error "gcloud command not found. Please install the Google Cloud SDK."
command -v docker >/dev/null 2>&1 || print_error "docker command not found. Please install Docker and ensure it is running."
command -v python3 >/dev/null 2>&1 || print_error "python3 command not found. Please install Python 3."
command -v pip >/dev/null 2>&1 || print_error "pip command not found. Please install pip."
print_success "All required tools are installed."

# --- 1. GATHER USER INPUT ---
print_info "Starting the automated setup for the Rumi-Analytica App."
echo "------------------------------------------------------------------"

print_prompt "Enter your GCP Project ID: "
read PROJECT_ID
print_prompt "Enter the GCP Region for your resources (e.g., us-central1): "
read REGION
print_prompt "Enter your GitHub Username: "
read GITHUB_USER
print_prompt "Enter your GitHub Repository Name (the name of your forked repo): "
read GITHUB_REPO
print_prompt "Enter a username for the backend's simple auth: "
read SIMPLE_AUTH_USERNAME
print_prompt "Enter a password for the backend's simple auth: "
read -s SIMPLE_AUTH_PASSWORD
echo ""

echo "------------------------------------------------------------------"
print_info "Configuration Summary:"
echo "Project ID:           $PROJECT_ID"
echo "Region:               $REGION"
echo "GitHub User:          $GITHUB_USER"
echo "GitHub Repo:          $GITHUB_REPO"
echo "Auth Username:        $SIMPLE_AUTH_USERNAME"
echo "------------------------------------------------------------------"
print_prompt "Is this correct? [y/N] "
read confirm
if [[ ! "$confirm" =~ ^[yY](es)?$ ]]; then echo "Setup cancelled."; exit 1; fi

# --- 2. SET VARIABLES AND CONFIGURE GCLOUD ---
print_info "Configuring gcloud to use project $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

APP_SA_NAME="rumi-app-runner-sa"
APP_SA_EMAIL="${APP_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
BUILD_SA_NAME="rumi-builder-sa"
BUILD_SA_EMAIL="${BUILD_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# --- 3. ENABLE APIS ---
print_info "Enabling necessary GCP APIs..."
gcloud services enable run.googleapis.com iam.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com bigquery.googleapis.com

# --- 4. CREATE SERVICE ACCOUNTS AND PERMISSIONS ---
print_info "Creating Service Account for the application runtime..."
gcloud iam service-accounts create "$APP_SA_NAME" --display-name="Rumi Analytica App Runner SA" || print_info "App Service Account already exists."

print_info "Granting App Service Account required roles (Vertex AI, BigQuery)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$APP_SA_EMAIL" --role="roles/aiplatform.user" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$APP_SA_EMAIL" --role="roles/bigquery.jobUser" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$APP_SA_EMAIL" --role="roles/bigquery.dataViewer" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$APP_SA_EMAIL" --role="roles/bigquery.user" --condition=None

print_info "Creating Service Account for Cloud Build..."
gcloud iam service-accounts create "$BUILD_SA_NAME" --display-name="Rumi Analytica Builder SA" || print_info "Build Service Account already exists."

print_info "Granting Cloud Build SA required roles (Cloud Run, Artifact Registry, IAM, Logging)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$BUILD_SA_EMAIL" --role="roles/run.admin" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$BUILD_SA_EMAIL" --role="roles/artifactregistry.writer" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$BUILD_SA_EMAIL" --role="roles/secretmanager.secretAccessor" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$BUILD_SA_EMAIL" --role="roles/logging.logWriter" --condition=None
gcloud iam service-accounts add-iam-policy-binding "$APP_SA_EMAIL" --member="serviceAccount:$BUILD_SA_EMAIL" --role="roles/iam.serviceAccountUser"

# --- 5. CREATE SECRETS ---
print_info "Creating secrets in Secret Manager..."
JWT_SECRET=$(openssl rand -base64 32)
echo "$JWT_SECRET" | gcloud secrets create RUMI_JWT_SECRET --data-file=- --replication-policy=automatic --quiet || (echo "$JWT_SECRET" | gcloud secrets versions add RUMI_JWT_SECRET --data-file=- --quiet && print_info "Secret RUMI_JWT_SECRET updated.")

# Use passlib and a specific, compatible bcrypt version (3.2.2) to hash the password
print_info "Installing passlib and a compatible bcrypt version (3.2.2)..."
pip install "passlib[bcrypt]" "bcrypt==3.2.2" > /dev/null
PASSWORD_HASH=$(python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('$SIMPLE_AUTH_PASSWORD'))")
pip uninstall -y "passlib[bcrypt]" "bcrypt" > /dev/null
print_info "Password hashed successfully using passlib."

echo -n "$PASSWORD_HASH" | gcloud secrets create RUMI_PASSWORD_HASH --data-file=- --replication-policy=automatic --quiet || (echo -n "$PASSWORD_HASH" | gcloud secrets versions add RUMI_PASSWORD_HASH --data-file=- --quiet && print_info "Secret RUMI_PASSWORD_HASH updated.")

print_info "Granting App Service Account access to secrets..."
gcloud secrets add-iam-policy-binding RUMI_JWT_SECRET --member="serviceAccount:$APP_SA_EMAIL" --role="roles/secretmanager.secretAccessor" --quiet
gcloud secrets add-iam-policy-binding RUMI_PASSWORD_HASH --member="serviceAccount:$APP_SA_EMAIL" --role="roles/secretmanager.secretAccessor" --quiet

# --- 6. CONFIGURE ARTIFACT REGISTRY AND DOCKER ---
print_info "Creating Artifact Registry repository 'rumi-analytica'..."
gcloud artifacts repositories create "rumi-analytica" --repository-format=docker --location="$REGION" --description="Docker repository for Rumi Analytica" || print_info "Artifact Registry repository already exists."
print_info "Configuring Docker to authenticate with Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# --- 7. INITIAL DEPLOYMENT ---
print_info "Starting initial deployment process..."
print_info "[1/3] Building and deploying backend for the first time..."
BACKEND_IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/rumi-analytica/backend:initial"
(cd backend && docker build -t "$BACKEND_IMAGE_TAG" .)
docker push "$BACKEND_IMAGE_TAG"

gcloud run deploy "rumi-analytica-backend" \
    --image="$BACKEND_IMAGE_TAG" \
    --service-account="$APP_SA_EMAIL" \
    --region="$REGION" \
    --platform="managed" \
    --allow-unauthenticated \
    --port="8080" \
    --set-env-vars="SIMPLE_AUTH_USERNAME=${SIMPLE_AUTH_USERNAME},GOOGLE_GENAI_USE_VERTEXAI=True" \
    --set-secrets="SIMPLE_AUTH_PASSWORD_HASH=RUMI_PASSWORD_HASH:latest,JWT_SECRET_KEY=RUMI_JWT_SECRET:latest"

BACKEND_URL=$(gcloud run services describe "rumi-analytica-backend" --region="$REGION" --format='value(status.url)')
print_success "Backend deployed. URL: $BACKEND_URL"

print_info "[2/3] Building and deploying frontend..."
FRONTEND_IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/rumi-analytica/frontend:initial"
(cd frontend && npm install && VITE_BACKEND_URL="$BACKEND_URL" npm run build && docker build -t "$FRONTEND_IMAGE_TAG" .)
docker push "$FRONTEND_IMAGE_TAG"

gcloud run deploy "rumi-analytica-frontend" \
    --image="$FRONTEND_IMAGE_TAG" \
    --region="$REGION" \
    --platform="managed" \
    --allow-unauthenticated \
    --port="8080"

FRONTEND_URL=$(gcloud run services describe "rumi-analytica-frontend" --region="$REGION" --format='value(status.url)')
print_success "Frontend deployed. URL: $FRONTEND_URL"

print_info "[3/3] Updating backend with frontend URL for CORS..."
gcloud run services update "rumi-analytica-backend" --region="$REGION" --update-env-vars="FRONTEND_URL=${FRONTEND_URL}"
print_success "Backend updated."

# --- 8. CREATE CLOUD BUILD TRIGGERS ---
print_info "Creating Cloud Build triggers (assuming GitHub connection is already established)..."
gcloud builds triggers create github \
    --name="deploy-rumi-backend-main" \
    --region="$REGION" \
    --repo-owner="$GITHUB_USER" \
    --repo-name="$GITHUB_REPO" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml" \
    --service-account="projects/${PROJECT_ID}/serviceAccounts/${BUILD_SA_EMAIL}" \
    --included-files="backend/**" \
    --substitutions="_SERVICE=backend,_BACKEND_URL=${BACKEND_URL},_FRONTEND_URL=${FRONTEND_URL},_SIMPLE_AUTH_USERNAME=${SIMPLE_AUTH_USERNAME}"

gcloud builds triggers create github \
    --name="deploy-rumi-frontend-main" \
    --region="$REGION" \
    --repo-owner="$GITHUB_USER" \
    --repo-name="$GITHUB_REPO" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml" \
    --service-account="projects/${PROJECT_ID}/serviceAccounts/${BUILD_SA_EMAIL}" \
    --included-files="frontend/**" \
    --substitutions="_SERVICE=frontend,_BACKEND_URL=${BACKEND_URL},_FRONTEND_URL=${FRONTEND_URL}"

# --- 9. FINAL OUTPUT ---
echo "------------------------------------------------------------------"
print_success "Setup Complete!"
echo ""
echo -e "Your application is deployed and available at:"
echo -e "Frontend: ${YELLOW}${FRONTEND_URL}${NC}"
echo -e "Backend:  ${YELLOW}${BACKEND_URL}${NC}"
echo ""
print_info "Two CI/CD triggers have been created in Cloud Build:"
echo "  - 'deploy-rumi-frontend-main': Triggers on pushes to 'frontend/**' in the main branch."
echo "  - 'deploy-rumi-backend-main': Triggers on pushes to 'backend/**' in the main branch."
echo ""
print_info "To change the password in the future, you must update the 'RUMI_PASSWORD_HASH' secret in Secret Manager."
print_info "You will need to generate a new bcrypt hash of your new password and use it to create a new version of the secret."
echo "------------------------------------------------------------------"