#!/bin/bash

BRANCH=$1

echo "Deploying preview for branch: $BRANCH"

# This script is responsible for deploying an ephemeral preview environment.
# It should interact with your chosen infrastructure (e.g., Docker, Kubernetes, a hosting provider).
#
# Placeholder for real deployment logic:
#
# --- Docker Example ---
# # Build and push Docker image
# docker build -t my-app:$BRANCH .
# docker push my-app:$BRANCH
#
# # Run Docker container (adjust port mapping and environment variables as needed)
# docker run -d --name preview-$BRANCH -p 80:3000 my-app:$BRANCH
#
# --- Kubernetes Example ---
# # Apply Kubernetes manifests, setting the image and namespace dynamically
# # Ensure you have a 'k8s/preview-deployment.yaml' that uses a placeholder for the image tag
# # and potentially the namespace.
# kubectl apply -f k8s/preview-deployment.yaml \
#   --set image.tag=$BRANCH \
#   --namespace=preview-$BRANCH
#
# --- Hosting Provider (Vercel/Netlify/Heroku) Example ---
# # For platforms like Vercel or Netlify, deployment often happens automatically via Git integration.
# # You might use their CLI for specific actions, e.g., triggering a build or linking a project.
# # Vercel CLI:
# # vercel deploy --prebuilt --prod -t $VERCEL_TOKEN # or similar commands
# # Heroku CLI:
# # heroku container:push web --app my-app-preview-$BRANCH -R $BRANCH
# # heroku container:release web --app my-app-preview-$BRANCH
#
# IMPORTANT: Ensure your CI/CD user/role has the necessary permissions (e.g., AWS IAM, GCP Service Account, Kubeconfig)
# to perform these deployment operations.

# Simulate a delay for deployment
sleep 5

# --- Output the Preview URL ---
# This is crucial. The workflow will capture this output to pass the URL to subsequent jobs.
# In a real scenario, this URL would be the actual public endpoint of your deployed application.
echo "Preview URL: https://preview-$BRANCH.example.com"
