import base64

with open('cookies.txt', 'r', encoding='utf-8') as f:
    content = f.read()

encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

print("=" * 60)
print("COPY EVERYTHING BELOW THIS LINE INTO RAILWAY's YT_COOKIES:")
print("=" * 60)
print(encoded)
print("=" * 60)
print(f"\nLength: {len(encoded)} characters")
