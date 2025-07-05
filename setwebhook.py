import requests

TOKEN = "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"
URL = f"https://SoLogin.pythonanywhere.com/{TOKEN}"

response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={URL}")

print(response.status_code)
print(response.text)