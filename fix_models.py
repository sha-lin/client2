
import os

file_path = r'C:\Users\Administrator\Desktop\client\clientapp\models.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines 1-1138 (indices 0-1137)
# Line 1138 is empty line after ProductTemplate
part1 = lines[:1138]

# Keep lines 1334-end (indices 1333-end)
# Line 1334 is start of correct TurnAroundTime class
part2 = lines[1333:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(part1 + part2)

print(f"Fixed {file_path}. New line count: {len(part1 + part2)}")
