from integrations.weather import get_weather


results = get_weather("Goa")

print("\n--- LIVE WEATHER ---")

for weather in results[:5]:
    print(weather)