```
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .Values.servicename }}-hpa
  labels:
    app: {{ .Values.servicename }}
    release: {{ .Release.Name }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ .Values.servicename }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
{{- range .Values.autoscaling.metrics }}
    - type: {{ .type }}
      {{- if eq .type "Resource" }}
      resource:
        name: {{ .resource.name }}
        target:
          type: {{ .target.type }}
          {{- if .target.averageUtilization }}
          averageUtilization: {{ .target.averageUtilization }}
          {{- end }}
          {{- if .target.averageValue }}
          averageValue: {{ .target.averageValue }}
          {{- end }}
      {{- else if eq .type "Pods" }}
      pods:
        metric:
          name: {{ .pods.metric.name }}
        target:
          type: {{ .pods.target.type }}
          averageValue: {{ .pods.target.averageValue }}
      {{- end }}
{{- end }}
{{- end }}









servicename: my-app-service

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue
          averageValue: 500Mi





apiVersion: batch/v1
kind: CronJob
metadata:
  name: metric-scaler-cron
  namespace: {{ .Values.namespace }}
spec:
  schedule: "{{ .Values.cronJob.schedule }}"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: measure-service-sa
          containers:
            - name: metric-scaler
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  # Fetch CPU and RAM usage
                  CPU_USAGE=$(kubectl top pod -n {{ .Values.namespace }} | grep {{ .Values.serviceName }} | awk '{print $2}' | sed 's/m//g' | awk '{s+=$1} END {print s}')
                  RAM_USAGE=$(kubectl top pod -n {{ .Values.namespace }} | grep {{ .Values.serviceName }} | awk '{print $3}' | sed 's/Mi//g' | awk '{s+=$1} END {print s}')
                  CPU_THRESHOLD={{ .Values.cronJob.cpuThreshold }}
                  RAM_THRESHOLD={{ .Values.cronJob.ramThreshold }}

                  # Fetch metric_count from Prometheus
                  PROMETHEUS_URL="http://prometheus:9090/api/v1/query?query={{ .Values.cronJob.metricName }}"
                  METRIC_COUNT=$(curl -s "$PROMETHEUS_URL" | jq '.data.result | length')

                  echo "Metric count: $METRIC_COUNT"
                  echo "CPU Usage: $CPU_USAGE m, RAM Usage: $RAM_USAGE Mi"

                  # Fetch current replicas
                  CURRENT_REPLICAS=$(kubectl get deployment {{ .Values.serviceName }} -n {{ .Values.namespace }} -o jsonpath='{.spec.replicas}')

                  # Scale Up Logic (CPU or RAM above threshold)
                  if [ "$CPU_USAGE" -gt "$CPU_THRESHOLD" ] || [ "$RAM_USAGE" -gt "$RAM_THRESHOLD" ]; then
                    NEW_REPLICAS=$((CURRENT_REPLICAS + 1))
                    echo "Scaling up to $NEW_REPLICAS replicas due to high CPU/RAM usage."
                    kubectl scale deployment {{ .Values.serviceName }} --replicas=$NEW_REPLICAS -n {{ .Values.namespace }}
                    exit 0
                  fi

                  # Scale Down Logic (metric_count == 0)
                  if [ "$METRIC_COUNT" -eq 0 ]; then
                    if [ "$CURRENT_REPLICAS" -gt 1 ]; then
                      NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
                      echo "Scaling down to $NEW_REPLICAS replicas due to metric_count = 0."
                      kubectl scale deployment {{ .Values.serviceName }} --replicas=$NEW_REPLICAS -n {{ .Values.namespace }}
                    else
                      echo "Only 1 replica remaining, no further scaling down."
                    fi
                  else
                    echo "Metric count > 0, keeping the current replica count."
                  fi
          restartPolicy: OnFailure





namespace: monitoring

cronJob:
  schedule: "*/5 * * * *"  # Runs every 5 minutes
  metricName: "service_metric"
  cpuThreshold: 200  # CPU threshold in millicores (m)
  ramThreshold: 500  # RAM threshold in MiB

serviceName: "measure-service"





git config --global --unset url.ssh://git@bitbucket.org.insteadOf
git config --global --unset user.name
git config --global --unset user.email

git config --global user.name "YourGitHubUsername"
git config --global user.email "your-email@example.com"






COUNT=$(grep -o '"severity":"High"' "$JSON_FILE" | wc -l || echo 0)
job4:
  needs: [job2, job3]
  if: always()  # Ensure Job4 always runs, even if Job2 and Job3 fail
  runs-on: ubuntu-latest
  steps:
    - name: Check if Job2 and Job3 both failed
      run: |
        if [[ "${{ needs.job2.result }}" == "failure" && "${{ needs.job3.result }}" == "failure" ]]; then
          echo "Both Job2 and Job3 failed. Failing Job4 to prevent merge."
          exit 1
        fi
        
    - name: Run Job4
      run: echo "Running Job 4"



apiVersion: v1
kind: ServiceAccount
metadata:
  name: measure-service-sa
  namespace: {{ .Values.namespace }}

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: measure-service-role
  namespace: {{ .Values.namespace }}
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: measure-service-rolebinding
  namespace: {{ .Values.namespace }}
subjects:
  - kind: ServiceAccount
    name: measure-service-sa
    namespace: {{ .Values.namespace }}
roleRef:
  kind: Role
  name: measure-service-role
  apiGroup: rbac.authorization.k8s.io





apiVersion: batch/v1
kind: CronJob
metadata:
  name: measure-metric-cron
  namespace: {{ .Values.namespace }}
spec:
  schedule: "{{ .Values.cronJob.schedule }}"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: measure-service-sa
          containers:
            - name: metric-collector
              image: busybox
              command:
                - /bin/sh
                - -c
                - |
                  echo "Fetching metric {{ .Values.cronJob.metricName }} from {{ .Values.serviceName }}"
                  curl -s "http://{{ .Values.serviceName }}:8080/metrics/{{ .Values.cronJob.metricName }}"
          restartPolicy: OnFailure





namespace: <namespace>
cronJob:
  schedule: "<schedule>"
  metricName: "<metric_name>"

serviceName: "measure-service"



apiVersion: v2
name: measure-service-chart
description: A Helm chart for deploying measure-service cron job
version: 1.0.0
appVersion: 1.0.0






name: Deploy Measure Service

on:
  workflow_dispatch:
    inputs:
      namespace:
        description: 'Kubernetes Namespace'
        required: true
      schedule:
        description: 'Cron Schedule'
        required: true
      metricName:
        description: 'Metric Name'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Replace placeholders in values.yaml
        run: |
          sed -i "s|<namespace>|${{ github.event.inputs.namespace }}|g" measure-service-chart/values.yaml
          sed -i "s|<schedule>|${{ github.event.inputs.schedule }}|g" measure-service-chart/values.yaml
          sed -i "s|<metric_name>|${{ github.event.inputs.metricName }}|g" measure-service-chart/values.yaml

      - name: Uninstall previous deployment
        run: |
          helm uninstall measure-service -n ${{ github.event.inputs.namespace }} || true
          sleep 20

      - name: Deploy Helm Chart
        run: |
          helm upgrade --install measure-service measure-service-chart -n ${{ github.event.inputs.namespace }}



name: Trigger Measure Service Deployment

on:
  push:
    branches:
      - main

jobs:
  trigger-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Deploy Workflow
        uses: benc-uk/workflow-dispatch@v1
        with:
          workflow: "Deploy Measure Service"
          token: ${{ secrets.GITHUB_TOKEN }}
          inputs: |
            namespace: "monitoring"
            schedule: "*/5 * * * *"
            metricName: "cpu_usage"


```











```

a=$(grep "grape" sample.txt || echo 0)

Allowed maintenance window:
April 12, 00:00 UTC → April 14, 00:00 UTC
Total: 48 hours ✅
Exclusions:
April 1 – April 7 ❌ (Blocks 7 days)
April 24 – April 30 ❌ (Blocks 7 days)
Total available upgrade time in April: Only 48 hours (April 12–14)
❌ Why It Fails?
GKE requires at least 48 hours of availability within ANY 32-day rolling window. Since you are blocking 14 out of 30 days, the system does not guarantee 48 hours in all cases.


locals {
  month = "03"  # Define the target month (March)
  year  = "2025" # Define the target year
}

module "gke_cluster" {
  source = "company/proprietary-gke-module"

  maintenance_start_time   = "${local.year}-${local.month}-01T00:00:00Z"
  maintenance_end_time     = "${local.year}-${local.month}-31T23:59:59Z"
  maintenance_recurrence   = "FREQ=DAILY"

  maintenance_exclusion = [
    {
      exclusion_name = "first-week-${local.month}"
      start_name     = "${local.year}-${local.month}-01T00:00:00Z"
      end_name       = "${local.year}-${local.month}-07T23:59:59Z"
      scope          = "NO_UPGRADES"
    },
    {
      exclusion_name = "last-week-${local.month}"
      start_name     = "${local.year}-${local.month}-25T00:00:00Z"
      end_name       = "${local.year}-${local.month}-31T23:59:59Z"
      scope          = "NO_UPGRADES"
    }
  ]
}

locals {
  year   = "2025"
  month  = "02"  # Change dynamically as needed
  days_in_month = {
    "01" = 31, "02" = 28, "03" = 31, "04" = 30,
    "05" = 31, "06" = 30, "07" = 31, "08" = 31,
    "09" = 30, "10" = 31, "11" = 30, "12" = 31
  }

  last_day_of_month = lookup(local.days_in_month, local.month)           # Get last day
  start_day = tostring(local.last_day_of_month - 6)  # Calculate start day (last day - 7)
}

module "gke_cluster" {
  source = "company/proprietary-gke-module"

  maintenance_exclusion = [
    {
      exclusion_name = "last-week-${local.month}"
      start_name     = "${local.year}-${local.month}-${local.start_day}T00:00:00Z"
      end_name       = "${local.year}-${local.month}-${local.last_day_of_month}T23:59:59Z"
      scope          = "NO_UPGRADES"
    }
  ]
}



createTime,responseId,promptTokenCount,candidateTokenCount,totalToeknCount,model_ver


{
    "model_name_1": {
      "Input price$/million": 0.10,
      "Output price$/million": 0.40
    },
    "model_name_2": {
      "Input price$/million": 0.12,
      "Output price$/million": 0.38
    },
    "model_name_3": {
      "Input price$/million": 0.11,
      "Output price$/million": 0.35
    }
}  

from flask import Flask, request, jsonify
import json
import requests  # Now using requests for simplicity

app = Flask(__name__)

# Metadata server URLs
METADATA_URL = "http://metadata.google.internal/computeMetadata/v1"
HEADERS = {"Metadata-Flavor": "Google"}

def get_metadata(path):
    """Fetches metadata from GCP metadata server."""
    response = requests.get(f"{METADATA_URL}/{path}", headers=HEADERS)
    return response.text

def get_project_id():
    return get_metadata("project/project-id")

def get_region():
    full_zone = get_metadata("instance/zone")  # e.g., projects/12345/zones/us-central1-a
    return full_zone.split("/")[-1].rsplit("-", 1)[0]  # Extracts 'us-central1' from 'us-central1-a'

def get_access_token():
    """Fetches an access token for authentication with Vertex AI."""
    response = requests.get(f"{METADATA_URL}/instance/service-accounts/default/token", headers=HEADERS)
    return response.json()["access_token"]

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("message", "")

    if not prompt:
        return jsonify({"error": "Message is required"}), 400

    project_id = get_project_id()
    region = get_region()
    
    # Vertex AI REST API Endpoint
    endpoint = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/publishers/google/models/gemini-pro:predict"

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"temperature": 0.7, "maxOutputTokens": 256}
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)














from flask import Flask, request, jsonify
import json
import urllib.request

app = Flask(__name__)

# Metadata server URLs
METADATA_URL = "http://metadata.google.internal/computeMetadata/v1"
HEADERS = {"Metadata-Flavor": "Google"}

def get_metadata(path):
    """Fetches metadata from GCP metadata server."""
    url = f"{METADATA_URL}/{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")

def get_project_id():
    return get_metadata("project/project-id")

def get_region():
    full_zone = get_metadata("instance/zone")  # e.g., projects/12345/zones/us-central1-a
    return full_zone.split("/")[-1].rsplit("-", 1)[0]  # Extracts 'us-central1' from 'us-central1-a'

def get_access_token():
    """Fetches an access token for authentication with Vertex AI."""
    url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        token_data = json.load(response)
        return token_data["access_token"]

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("message", "")

    if not prompt:
        return jsonify({"error": "Message is required"}), 400

    project_id = get_project_id()
    region = get_region()
    
    # Vertex AI REST API Endpoint
    endpoint = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/publishers/google/models/gemini-pro:predict"

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "instances": [{"prompt": prompt}],
        "parameters": {"temperature": 0.7, "maxOutputTokens": 256}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(endpoint, data=payload, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.load(response)
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

```



```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 50px;
        }
        #chat-container {
            width: 300px;
            margin: auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }
        textarea {
            width: 100%;
            height: 80px;
            margin-bottom: 10px;
            padding: 5px;
        }
        button {
            padding: 10px 20px;
            border: none;
            background-color: #007bff;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <h2>Chatbot</h2>
        <textarea id="query" placeholder="Type your message..."></textarea>
        <br>
        <button onclick="sendMessage()">Send</button>
        <p id="response"></p>
    </div>

    <script>
        function sendMessage() {
            const query = document.getElementById('query').value;

            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ Query: query })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('response').textContent = data.reply || "No response.";
            })
            .catch(error => {
                document.getElementById('response').textContent = "Error: " + error;
            });
        }
    </script>
</body>
</html>





#!/bin/bash

# Check if a file is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <json-file>"
    exit 1
fi

JSON_FILE="$1"

# Check if the file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "Error: File '$JSON_FILE' not found!"
    exit 1
fi

# Count occurrences of "severity":"High"
COUNT=$(grep -o '"severity":"High"' "$JSON_FILE" | wc -l)

echo "Occurrences of \"severity\":\"High\": $COUNT"





#!/bin/bash
set -e

# Get the first file in the reports/ directory
REPORT_FILE=$(ls -1 reports/ | head -n 1)

# Check if a file was found
if [ -z "$REPORT_FILE" ]; then
  echo "Error: No report file found in reports/ directory!"
  exit 1
fi

# Full path to the report file
REPORT_PATH="reports/$REPORT_FILE"

# Check if the file exists
if [ ! -f "$REPORT_PATH" ]; then
  echo "Error: $REPORT_PATH not found!"
  exit 1
fi

echo "Processing report: $REPORT_FILE"

# Extract values from the first index of the "result" array using jq
CRITICAL=$(jq -r '.result[0].vulnerabilities.vulnerabilitydistribution.critical // 0' "$REPORT_PATH")
HIGH=$(jq -r '.result[0].vulnerabilities.vulnerabilitydistribution.high // 0' "$REPORT_PATH")

# Calculate the total vulnerabilities
TOTAL=$((CRITICAL + HIGH))

echo "Critical Vulnerabilities: $CRITICAL"
echo "High Vulnerabilities: $HIGH"
echo "Total Vulnerabilities: $TOTAL"

# If total vulnerabilities are greater than zero, exit with a non-zero code to fail the workflow.
if [ "$TOTAL" -gt 0 ]; then
  echo "Vulnerabilities found! Failing the workflow."
  exit 1
else
  echo "No vulnerabilities found."
  exit 0
fi








#!/bin/bash

# Path to the JSON report file
REPORT_FILE="report.json"

# Check if the file exists
if [ ! -f "$REPORT_FILE" ]; then
  echo "Error: $REPORT_FILE not found!"
  exit 1
fi

# Extract values using jq
CRITICAL=$(jq -r '.result.vulnerabilities.vulnerabilitydistribution.critical // 0' "$REPORT_FILE")
HIGH=$(jq -r '.result.vulnerabilities.vulnerabilitydistribution.high // 0' "$REPORT_FILE")

# Print results
echo "Critical Vulnerabilities: $CRITICAL"
echo "High Vulnerabilities: $HIGH"



curl -L -H "Authorization: token YOUR_GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     -o artifact.zip \
     https://api.github.com/repos/OWNER/REPO/actions/artifacts/ARTIFACT_ID/zip



curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/OWNER/REPO/actions/runs/RUN_ID/artifacts



jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Create artifact
        run: echo "Hello, World!" > artifact.txt

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: my-artifact
          path: artifact.txt

  download:
    runs-on: ubuntu-latest
    needs: build  # Ensures build runs first
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: my-artifact
          path: ./downloaded-artifact

      - name: List downloaded files
        run: ls -R ./downloaded-artifact
```









```
name: Deploy to GKE

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v3

    - name: Set up Google Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        version: 'latest'
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}

    - name: Authenticate kubectl
      run: |
        gcloud container clusters get-credentials ${{ secrets.GKE_CLUSTER_NAME }} --zone ${{ secrets.GKE_ZONE }}

    - name: Deploy Application
      run: |
        kubectl apply -f k8s/
        kubectl rollout status deployment/<deployment-name> -n <namespace>

    - name: Check DNS Pod Status
      run: |
        echo "Checking CoreDNS status..."
        kubectl get pods -n kube-system | grep coredns

    - name: Validate Consul Service
      run: |
        echo "Validating Consul service..."
        kubectl get svc -n <namespace>
        kubectl describe svc consul -n <namespace>

    - name: Test DNS Resolution
      run: |
        echo "Creating a test pod to check DNS resolution..."
        kubectl run test-dns --image=busybox --restart=Never --command -- sleep 3600
        kubectl wait --for=condition=ready pod/test-dns --timeout=60s
        kubectl exec test-dns -- nslookup consul.<namespace>.svc.cluster.local

    - name: Check Logs for Consul Pod
      run: |
        echo "Checking Consul pod logs..."
        kubectl logs deployment/consul -n <namespace>

    - name: Apply Network Policies (if needed)
      run: |
        echo "Applying network policies to allow DNS traffic..."
        cat <<EOF | kubectl apply -f -
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        metadata:
          name: allow-dns
          namespace: <namespace>
        spec:
          podSelector: {}
          policyTypes:
            - Ingress
          ingress:
            - from:
                - namespaceSelector: {}
              ports:
                - protocol: UDP
                  port: 53
                - protocol: TCP
                  port: 53
        EOF

    - name: Restart Pods if DNS Changes
      run: |
        echo "Restarting deployment to apply DNS fixes..."
        kubectl rollout restart deployment/<deployment-name> -n <namespace>

```


```
import jwt  # Install using `pip install pyjwt[crypto]`
import datetime
import json
import requests

def generate_jwt(service_account_info, audience):
    """
    Generates a signed JWT for Google service account authentication.
    :param service_account_info: The JSON key as a dictionary.
    :param audience: The API audience (e.g., https://storage.googleapis.com/).
    :return: Signed JWT.
    """
    now = datetime.datetime.utcnow()
    payload = {
        "iss": service_account_info["client_email"],
        "sub": service_account_info["client_email"],
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(minutes=60)).timestamp()),
    }
    headers = {"alg": "RS256", "typ": "JWT"}
    signed_jwt = jwt.encode(payload, service_account_info["private_key"], algorithm="RS256", headers=headers)
    return signed_jwt



def get_access_token(signed_jwt):
    """
    Exchanges a signed JWT for an OAuth 2.0 access token.
    :param signed_jwt: The signed JWT.
    :return: Access token.
    """
    token_url = "https://oauth2.googleapis.com/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": signed_jwt,
    }
    response = requests.post(token_url, headers=headers, data=payload)
    response_data = response.json()
    return response_data["access_token"]



def upload_to_gcs_via_api(bucket_name, object_name, data, access_token):
    """
    Uploads data to GCS using the JSON API.
    :param bucket_name: Name of the GCS bucket.
    :param object_name: Destination object name in the bucket.
    :param data: Data to upload (as bytes).
    :param access_token: OAuth 2.0 access token.
    """
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={object_name}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        print(f"File uploaded successfully: {response.json()}")
    else:
        print(f"Failed to upload file: {response.status_code}, {response.text}")



import json

# Replace this with your service account key file
SERVICE_ACCOUNT_KEY = "service_account_key.json"

# Load the service account key
with open(SERVICE_ACCOUNT_KEY, "r") as f:
    service_account_info = json.load(f)

# Step 1: Generate a signed JWT
audience = "https://storage.googleapis.com/"
signed_jwt = generate_jwt(service_account_info, audience)

# Step 2: Get an OAuth 2.0 access token
access_token = get_access_token(signed_jwt)

# Step 3: Upload a file to GCS
bucket_name = "your-bucket-name"
object_name = "test-file.txt"
data = b"This is some test data to upload to GCS."  # Replace with your actual data
upload_to_gcs_via_api(bucket_name, object_name, data, access_token)


```



```
pip install google-cloud-storage


from google.cloud import storage

def upload_to_gcs(bucket_name, file_path, destination_blob_name):
    """
    Uploads a file to a Google Cloud Storage bucket.
    :param bucket_name: The name of the GCS bucket.
    :param file_path: Local path to the file to upload.
    :param destination_blob_name: Destination file name in the bucket.
    """
    try:
        # Initialize the GCS client
        storage_client = storage.Client()

        # Get the bucket
        bucket = storage_client.bucket(bucket_name)

        # Create a new blob and upload the file's content
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)

        print(f"File {file_path} uploaded to {destination_blob_name} in bucket {bucket_name}.")

    except Exception as e:
        print(f"An error occurred: {e}")


```


```
sed -i '' "s/^default_ccache_name = KEYRING:persistent:%{uid}/default_ccache_name = \/tmp\/hello:%{uid}/g" test.txt

# Environment Variable (Optional, outside Terraform)
# During Cloud Run deployment, set an environment variable named TARGET_IP with the value 123.123.13.2412.

resource "google_compute_firewall" "allow_outbound_to_intranet" {
  name    = "allow-outbound-to-intranet"
  network = google_compute_network.default.id

  allow {
    protocol = "tcp"
    ports    = ["80", "443"] # Adjust ports as needed
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags    = ["your-cloud-run-service-tag"]

  destination_ranges = ["123.123.13.2412"]
}

#!/bin/bash

# Replace 'your_target_ip' with the actual IP address of 'xyz.intranet.com'
echo "your_target_ip xyz.intranet.com" >> /etc/hosts
```



```
from flask import Flask, Blueprint, request, jsonify

weather_blueprint = Blueprint("weather", __name__)

@weather_blueprint.route("/fetch-weather", methods=["POST"])
def fetch_weather():
    # Simulate fetching weather data
    city = request.json.get("city")
    if not city:
        return jsonify({"error": "City not provided"}), 400

    weather_data = {
        "London": {"temperature": 12, "condition": "Cloudy"},
        "Delhi": {"temperature": 28, "condition": "Sunny"}
    }
    return jsonify(weather_data.get(city, {"error": "City not found"})), 200

# Create Flask app and register the Blueprint
app = Flask(__name__)
app.register_blueprint(weather_blueprint)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

```

variables.tf
```
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "schedule_frequency" {
  description = "Frequency for Cloud Scheduler (Cron format)"
  type        = string
  default     = "0 * * * *" # Every hour
}

```

pubsub.tf
```
resource "google_pubsub_topic" "weather_topic" {
  name = "weather-topic"
}
```

cloud_run.tf
```
resource "google_cloud_run_service" "weather_service" {
  name     = "weather-service"
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/weather-service:latest" # Replace with your image name
        env {
          name  = "PORT"
          value = "8080"
        }
      }
    }
  }

  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "invoker" {
  service     = google_cloud_run_service.weather_service.name
  location    = google_cloud_run_service.weather_service.location
  project     = google_cloud_run_service.weather_service.project
  role        = "roles/run.invoker"
  member      = "serviceAccount:${google_project_service_account.scheduler_service_account.email}"
}
```

service_account.tf

```
resource "google_service_account" "scheduler_service_account" {
  account_id   = "scheduler-service-account"
  display_name = "Scheduler Service Account"
}

resource "google_project_iam_member" "pubsub_publisher" {
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.scheduler_service_account.email}"
}
```

scheduler.tf
```
resource "google_cloud_scheduler_job" "weather_scheduler" {
  name        = "weather-scheduler"
  description = "Triggers weather fetch job"
  schedule    = var.schedule_frequency
  time_zone   = "UTC"
  project     = var.project_id
  region      = var.region

  pubsub_target {
    topic_name = google_pubsub_topic.weather_topic.name
    data       = base64encode(jsonencode({ "city": "London" })) # For London; configure for Delhi in another job
  }

  attempt_deadline = "60s"

  oidc_token {
    service_account_email = google_service_account.scheduler_service_account.email
  }
}
```
pubsub_to_cloudrun.tf
```
resource "google_pubsub_subscription" "weather_subscription" {
  name  = "weather-subscription"
  topic = google_pubsub_topic.weather_topic.name

  push_config {
    push_endpoint = google_cloud_run_service.weather_service.status[0].url + "/fetch-weather"
    oidc_token {
      service_account_email = google_service_account.scheduler_service_account.email
    }
  }
}
```




```
resource "google_cloud_scheduler_job" "job" {
  for_each = var.cloud_scheduler_jobs

  name        = each.value.name
  description = each.value.desc
  schedule    = each.value.schedule
  time_zone   = "UTC" # Adjust if needed
  project     = each.value.project
  region      = each.value.region

  http_target {
    uri         = each.value.endpoint
    http_method = each.value.http_method

    # Optional headers, if provided
    headers = each.value.headers

    # Optional body for POST requests
    body = each.value.http_method == "POST" ? base64encode("{\"key\": \"value\"}") : null
  }
}

resource "google_cloud_scheduler_job" "job" {
  for_each = var.cloud_scheduler_jobs

  name        = each.value.name
  description = each.value.desc
  schedule    = each.value.schedule
  time_zone   = "UTC" # Adjust if needed
  project     = each.value.project
  region      = each.value.region

  http_target {
    uri         = each.value.endpoint
    http_method = each.value.http_method

    # Optional headers, if provided
    headers = each.value.headers

    # Optional body for POST requests
    body = each.value.http_method == "POST" ? base64encode("{\"key\": \"value\"}") : null
  }
}

```

