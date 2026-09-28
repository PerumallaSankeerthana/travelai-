from integrations.openai import generate_json


TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string"
        },
        "number": {
            "type": "integer"
        }
    },
    "required": [
        "message",
        "number"
    ]
}


print("\n--- GEMINI TEST ---")

result = generate_json(
    system_prompt=(
        "Return a simple JSON object. "
        "The message must say Gemini is working. "
        "The number must be 123."
    ),
    user_message="Test the Gemini API.",
    response_schema=TEST_SCHEMA,
)

print(result)