import base64
import zlib

with open('cookies.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Filter to only keep what we absolutely need (makes it way smaller)
clean_lines = []
for line in lines:
    if line.startswith('#') or '.youtube.com' in line or '.google.com' in line:
        clean_lines.append(line)

content = "".join(clean_lines).encode('utf-8')

# Compress it using zlib to make it extremely tiny!
compressed = zlib.compress(content)

# Add "ZLIB_" prefix so our app knows it's compressed
encoded = "ZLIB_" + base64.b64encode(compressed).decode('utf-8')

print("=" * 60)
print("COPY EVERYTHING BELOW THIS LINE INTO RAILWAY's YT_COOKIES:")
print("=" * 60)
print(encoded)
print("=" * 60)
print(f"\nLength: {len(encoded)} characters (Limit is 32768)")
