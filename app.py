from flask import Flask, request, jsonify
from uuid import uuid4
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient

from ml.predictor import load_model, predict_occupancy, get_model_info

load_dotenv()

app = Flask(__name__)
load_model()
azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_name = os.getenv("TABLE_NAME", "motionEvents")

table_client = None
if azure_storage_connection_string:
    table_service_client = TableServiceClient.from_connection_string(azure_storage_connection_string)
    table_client = table_service_client.create_table_if_not_exists(table_name)

@app.route("/motion", methods=["POST"])
def motion():
    if table_client is None:
        return jsonify(
            {
                "error": "Azure Table Storage is not configured",
                "hint": "Set AZURE_STORAGE_CONNECTION_STRING (and optionally TABLE_NAME) in .env",
            }
        ), 500

    data = request.get_json(silent=True)

    if data is None:
        raw = (request.get_data(as_text=True) or "").strip()
        if raw.startswith("'") and raw.endswith("'") and len(raw) >= 2:
            raw = raw[1:-1]
        try:
            data = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            data = None

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "No data received"}), 400

    device_id = (
        data.get("device_id")
        or data.get("device-id")
        or data.get("device.id")
    )
    motion_detected = data.get("motion")

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400

    if isinstance(motion_detected, str):
        motion_detected = motion_detected.strip().lower() in ("1", "true", "t", "yes", "y", "on")

    event = {
        "id": str(uuid4()),
        "device_id": device_id,
        "motion": bool(motion_detected),
        "received_at": datetime.now(timezone.utc).isoformat()
    }

    entity = {
        "PartitionKey": device_id,
        "RowKey": event["id"],
        "device_id": event["device_id"],
        "motion": event["motion"],
        "received_at": event["received_at"],
    }
    table_client.upsert_entity(mode="merge", entity=entity)

    received_dt = datetime.fromisoformat(event["received_at"])
    try:
        ai_result = predict_occupancy(event["motion"], received_dt)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503

    entity["prediction"] = ai_result["prediction"]
    entity["confidence"] = ai_result["confidence"]
    table_client.upsert_entity(mode="merge", entity=entity)

    return jsonify({
        "message": "Event added successfully",
        "event": event,
        "prediction": ai_result["prediction"],
        "led_command": ai_result["led_command"],
        "confidence": ai_result["confidence"],
        "model": ai_result["model"],
    }), 200

@app.route("/api/model", methods=["GET"])
def model_status():
    return jsonify(get_model_info()), 200


@app.route("/api/events", methods=["GET"])
def get_events():
    if table_client is None:
        return jsonify(
            {
                "error": "Azure Table Storage is not configured",
                "hint": "Set AZURE_STORAGE_CONNECTION_STRING (and optionally TABLE_NAME) in .env",
            }
        ), 500

    events = []
    for e in table_client.list_entities(results_per_page=200):
        events.append(
            {
                "id": e.get("RowKey"),
                "device_id": e.get("device_id") or e.get("PartitionKey"),
                "motion": bool(e.get("motion")),
                "received_at": e.get("received_at"),
                "prediction": e.get("prediction"),
                "confidence": e.get("confidence"),
            }
        )

    events.sort(key=lambda x: x.get("received_at") or "", reverse=True)
    return jsonify({"events": events}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    print("Server is running on port 5000")


