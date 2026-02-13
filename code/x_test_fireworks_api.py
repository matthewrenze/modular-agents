import os
from fireworks import Fireworks

api_key = os.environ.get("FIREWORKS_API_KEY")

client = Fireworks(api_key=api_key)

response = client.chat.completions.create(
  model="accounts/fireworks/models/deepseek-v3p1",
  messages=[{
    "role": "user",
    "content": "Say hello in Spanish",
  }],
)

print(response.choices[0].message.content)

# Get tokens
cached_tokens = getattr(response.usage.prompt_tokens_details, "cached_tokens", 0)
prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
completion_tokens = getattr(response.usage, "completion_tokens", 0)

# Accumulate tokens
print(f"cached_tokens {cached_tokens}")
print(f"input_tokens {prompt_tokens - cached_tokens}")
print(f"output_tokens {completion_tokens}")
print(f"total_tokens {getattr(response.usage, "total_tokens", 0)}")
