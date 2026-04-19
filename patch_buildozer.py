import os

bpath = os.popen('python -c "import buildozer; import os; print(os.path.dirname(buildozer.__file__))"').read().strip()
f = bpath + "/targets/android.py"
content = open(f).read()

old = "self.android_sdk_dir, 'tools', 'bin', 'sdkmanager'"
new = "self.android_sdk_dir, 'cmdline-tools', 'latest', 'bin', 'sdkmanager'"

if old in content:
    content = content.replace(old, new)
    open(f, 'w').write(content)
    print("SUCCESS: patched")
else:
    print("NOT FOUND - printing sdkmanager lines:")
    for i, line in enumerate(content.split('\n')):
        if 'sdkmanager' in line.lower() and ('join' in line or 'path' in line):
            print(f"  {i}: {line}")
