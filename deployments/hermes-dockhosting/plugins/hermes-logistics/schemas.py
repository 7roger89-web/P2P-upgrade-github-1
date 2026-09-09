"""Hermes tool schemas for the read-only Logistics connector.

These dicts are what the LLM sees. The handlers in ``tools.py`` execute a real
read-only MongoDB query; they never answer from memory or instruct the model
to "remember" Logistics data. Natural-language presentation stays in the model;
factual retrieval stays in the connector.
"""

TODAY_WORK_SCHEMA = {
    "name": "logistics_today_work",
    "description": (
        "Read-only: list the actionable Logistics items for a target day "
        "(Việc cần xử lý hôm nay). Returns shipment/task references, short "
        "action/status, and source provenance. Data comes from the Logistics "
        "datastore. If no items exist, returns NOT_FOUND. Never invents work."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": (
                    "Target date as ISO YYYY-MM-DD. Defaults to today in "
                    "Asia/Ho_Chi_Minh (UTC+7). Optional."
                ),
            }
        },
        "required": [],
    },
}

FREIGHT_RATE_SCHEMA = {
    "name": "logistics_freight_rate_lookup",
    "description": (
        "Read-only: current/recent freight rate from origin to destination for "
        "a container size or vehicle type. Returns status FOUND / NOT_FOUND / "
        "AMBIGUOUS, plus rate, currency, origin, destination, container, "
        "effective date, and recent history when supported. Data comes from the "
        "Logistics rate cards. Never invents a rate."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Origin place/port/city (e.g. 'Hải Phòng').",
            },
            "destination": {
                "type": "string",
                "description": "Destination place/port/city (e.g. 'Hà Nội').",
            },
            "container": {
                "type": "string",
                "description": (
                    "Container size or vehicle type (e.g. \"20'\", \"40'\", "
                    "\"20' DV\", 'xe tải')."
                ),
            },
            "date": {
                "type": "string",
                "description": (
                    "Optional effective date as ISO YYYY-MM-DD. When omitted, "
                    "the most recent applicable rate is returned."
                ),
            },
        },
        "required": ["origin", "destination", "container"],
    },
}

SHIPMENT_STATUS_SCHEMA = {
    "name": "logistics_shipment_status",
    "description": (
        "Read-only: exact current status of a Logistics shipment by its id or "
        "reference. Returns the current stage/action and updated timestamp when "
        "available. Data comes from the Logistics datastore. Unknown id returns "
        "NOT_FOUND. Never invents a status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "shipment_id": {
                "type": "string",
                "description": "Shipment id / reference / code (e.g. 'LOHANG-001').",
            }
        },
        "required": ["shipment_id"],
    },
}

ALL_SCHEMAS = [
    TODAY_WORK_SCHEMA,
    FREIGHT_RATE_SCHEMA,
    SHIPMENT_STATUS_SCHEMA,
]
