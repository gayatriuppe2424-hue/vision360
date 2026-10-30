# cleaner.py
file_path = "vision360_ui.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the invisible non-breaking space with a standard space
content = content.replace("\xa0", " ")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("File cleaned successfully! You can now run vision360_ui.py")