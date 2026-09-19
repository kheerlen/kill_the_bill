from anthropic import Anthropic
from dotenv import load_dotenv
import base64
import json
import os
import time

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def parse_receipt(image_path: str) -> dict:
    """
    Parse a receipt image and return structured JSON as a Python dict.
    """

    ext = image_path.lower().split(".")[-1]
    media_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }

    if ext not in media_type_map:
        raise ValueError(f"Unsupported image format: {ext}")

    media_type = media_type_map[ext]

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    start = time.perf_counter()

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": """
Extract the receipt data from this image.

Return raw JSON only.
Do not use markdown.
Do not wrap the answer in ```json.

Use exactly this format:

{
  "merchant": "",
  "date": "",
  "currency": "",
  "items": [
    {
      "name": "",
      "description": "",
      "quantity": 1,
      "unit_price": 0.0,
      "total_price": 0.0
    }
  ],
  "subtotal": 0.0,
  "tax": 0.0,
  "total": 0.0
}

"description" must be short, simple, generic, and useful for splitting a bill.

It should help a normal user distinguish items from each other.

Describe the most recognizable distinguishing trait of the item, such as:
- category (drink, dessert, side, household item)
- main type (sandwich, soup, pastry, medicine)
- key ingredient (cheese, vegetable, seafood)
- preparation style (fried, grilled, iced, sparkling)
- flavor/style (spicy, sweet, dark roast)

Good examples:
- "sparkling water"
- "iced coffee"
- "vegetable soup"
- "seafood pasta"
- "cheese pastry"
- "spicy sauce"
- "chocolate dessert"
- "potato side"
- "household item"
- "medicine"

Bad examples:
- "food"
- "dish"
- "item"
- "meal"
- "drink"

Keep descriptions broad, human-friendly, and no longer than a few words.
Do not simply repeat the full item name unless necessary.
"""
                    },
                ],
            }
        ],
    )
    
    elapsed = time.perf_counter() - start
    print(f"\nClaude latency: {elapsed:.2f}s")
    print("Claude token usage:")
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    estimated_cost = (input_tokens / 1_000_000) * 3 + (output_tokens / 1_000_000) * 15
    print(f"Estimated cost: ${estimated_cost:.4f}")

    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise RuntimeError(
            f"Claude returned no text (stop_reason={response.stop_reason}); "
            "try again or increase max_tokens"
        )
    text = text_blocks[0].strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json").removesuffix("```").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").removesuffix("```").strip()

    return json.loads(text)