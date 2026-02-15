# 📦 Publishing to PyPI

This guide will help you publish FK Path Finder to PyPI so users can `pip install fk-path-finder`.

## ✅ Status: READY TO PUBLISH

Your package has been built and verified:
- ✅ `dist/fk_path_finder-0.1.0.tar.gz` (source distribution)
- ✅ `dist/fk_path_finder-0.1.0-py3-none-any.whl` (wheel)
- ✅ Twine validation: PASSED

---

## 🚀 Quick Publish (Test First!)

### Step 1: Test on TestPyPI (RECOMMENDED)

**Create TestPyPI Account:**
1. Go to https://test.pypi.org/account/register/
2. Verify email
3. Go to https://test.pypi.org/manage/account/#api-tokens
4. Create API token (scope: "Entire account")
5. Copy the token (starts with `pypi-`)

**Upload to TestPyPI:**
```bash
py -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: paste your TestPyPI API token

**Test the installation:**
```bash
pip install --index-url https://test.pypi.org/simple/ fk-path-finder
```

If it works: ✅ Move to Step 2

---

### Step 2: Publish to Real PyPI

**Create PyPI Account:**
1. Go to https://pypi.org/account/register/
2. Verify email
3. Go to https://pypi.org/manage/account/#api-tokens
4. Create API token (scope: "Entire account")
5. Copy the token (starts with `pypi-`)

**Upload to PyPI:**
```bash
py -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: paste your PyPI API token

**Verify:**
- Visit: https://pypi.org/project/fk-path-finder/
- Should show your package!

---

## 📝 Alternative: Using .pypirc File

Create `~/.pypirc` (or `%USERPROFILE%\.pypirc` on Windows):

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

Then upload without prompts:
```bash
py -m twine upload --repository testpypi dist/*  # Test first
py -m twine upload dist/*                           # Real PyPI
```

---

## 🔄 If You Need to Rebuild

```bash
# Clean old builds
rmdir /s /q dist

# Rebuild
py -m build

# Check
py -m twine check dist/*
```

---

## ⚠️ Important Notes

1. **Version Numbers**: Once you publish a version (e.g., 0.1.0), you CANNOT upload it again. You must bump the version in `pyproject.toml`.

2. **Name Availability**: The name `fk-path-finder` is available (checked). If taken, update `pyproject.toml` name field.

3. **Dependencies**: The package depends on:
   - `mysql-connector-python>=8.0.0`
   - `rich>=13.0.0`
   - `click>=8.0.0`

4. **After Publishing**: Update README.md to change the PyPI badge back to the correct link.

---

## 🎯 After Publishing Checklist

- [ ] Package visible on https://pypi.org/project/fk-path-finder/
- [ ] `pip install fk-path-finder` works
- [ ] Update README badge: `[![PyPI](https://img.shields.io/pypi/v/fk-path-finder.svg)](https://pypi.org/project/fk-path-finder/)`
- [ ] Create GitHub Release v0.1.0
- [ ] Tweet/share your new package! 🎉

---

## 📞 Troubleshooting

**Error: File already exists**
- You already published this version
- Bump version in `pyproject.toml`

**Error: Invalid API Token**
- Make sure you're using `__token__` as username
- Copy the full token including `pypi-` prefix

**Error: 403 Forbidden**
- You don't have permission to this package name
- Choose a different name in `pyproject.toml`

---

## 🎉 Success!

Once published, anyone can:
```bash
pip install fk-path-finder
```

Your package will be live on PyPI forever! 🚀
