import base64

with open('cookies.txt', 'r', encoding='utf-8') as f:
    content = f.read().replace('\n', '').strip()

# Decode the cookies back to normal text
decoded = base64.b64decode(content).decode('utf-8')

with open('cookies.txt', 'w', encoding='utf-8') as f:
    f.write(decoded)

print("Restored cookies.txt back to normal!")
