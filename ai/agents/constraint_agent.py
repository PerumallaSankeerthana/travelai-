import json

from integrations.openai import generate_json


CONSTRAINT_SCHEMA = {
    "type": "object",
    "properties": {
        "origin": {
            "type": "string",
            "description": "Departure airport IATA code."
        },
        "destination": {
            "type": "string",
            "description": "Travel destination."
        },
        "destination_code": {
            "type": "string",
            "description": "Destination airport IATA code."
        },
        "start_date": {
            "type": "string",
            "description": "Trip start date in YYYY-MM-DD format."
        },
        "end_date": {
            "type": "string",
            "description": "Trip end date in YYYY-MM-DD format."
        },
        "travelers": {
            "type": "integer",
            "description": "Number of travelers."
        },
        "budget": {
            "type": "integer",
            "description": "Total travel budget in INR."
        },
        "preferences": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "User travel preferences."
        },
    },
    "required": [
        "origin",
        "destination",
        "destination_code",
        "start_date",
        "end_date",
        "travelers",
        "budget",
        "preferences",
    ],
}


SYSTEM_PROMPT = """
You extract travel constraints from a user's travel request.

Extract:

- origin airport IATA code
- destination
- destination airport IATA code
- start date
- end date
- number of travelers
- total budget in INR
- travel preferences

Rules:

- Dates must use YYYY-MM-DD.
- travelers must be an integer.
- budget must be an integer.
- preferences must be a list of strings.
- origin must be an airport IATA code.
- destination_code must be an airport IATA code.
- Return only the requested structured data.
"""


def extract_constraints(
    user_message: str
) -> dict:

    content = generate_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_schema=CONSTRAINT_SCHEMA,
    )

    if not content:
        raise RuntimeError(
            "Constraint Agent returned empty response"
        )

    try:
        return json.loads(content)

    except json.JSONDecodeError as exc:

        print("\nCONSTRAINT RESPONSE:")
        print(content)

        raise RuntimeError(
            "Constraint Agent returned invalid JSON"
        ) from exc