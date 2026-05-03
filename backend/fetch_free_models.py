import requests

resp = requests.get("https://openrouter.ai/api/v1/models")
models = resp.json().get("data", [])

free_models = []
for m in models:
    if "pricing" in m:
        p = m["pricing"]
        # Treat as free if both prompt and completion are "0"
        if p.get("prompt") == "0" and p.get("completion") == "0":
            free_models.append(m["id"])
        elif m["id"].endswith(":free"):
            if m["id"] not in free_models:
                free_models.append(m["id"])

print(f"Found {len(free_models)} free models:")
for m in free_models:
    print(f"- {m}")
