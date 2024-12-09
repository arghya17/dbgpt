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

