import difflib
line1 = "abcd"
line2 = "decd"
Differ = difflib.Differ()
diff = list(Differ.compare(line1, line2))
print(diff)
