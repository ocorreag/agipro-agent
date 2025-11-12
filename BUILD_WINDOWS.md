# Windows Build Instructions - IMPORTANT!

## ⚠️ The Error You're Seeing

The error `AttributeError: 'NoneType' object has no attribute 'buffer'` means you're running an **OLD executable** that was built BEFORE the fixes were applied.

## ✅ The Fix Has Been Applied

The `src/launcher.py` file has been fixed (lines 22-32 now have safety checks for None stdout/stderr).

## 🔨 You Must Rebuild the Executable

### Option 1: Clean Build (Recommended)
```bash
# On Windows, in Command Prompt or PowerShell:

# 1. Delete old build artifacts
rmdir /s /q build
rmdir /s /q dist
del *.spec

# 2. Rebuild with PyInstaller
cd C:\path\to\agipro_agent
pyinstaller --clean --noconfirm build_config\causa_agent.spec

# Or if you have the build script:
python build_scripts\build_local.py
```

### Option 2: Quick Rebuild
```bash
# Just rebuild (might use cached files)
pyinstaller build_config\causa_agent.spec
```

## 📁 Executable Location

After rebuilding, your new executable will be in:
- `dist/CAUSA-Agent.exe` (Windows)
- Make sure you're running the NEW exe from `dist/` folder
- Delete any old copies to avoid confusion

## 🧹 Clean Build Checklist

1. **Delete old build folders:**
   - `build/` folder
   - `dist/` folder
   - Any `.spec` files in root (not in build_config/)

2. **Clear PyInstaller cache:**
   ```bash
   # Windows
   rmdir /s /q %APPDATA%\pyinstaller

   # Or manually delete:
   # C:\Users\YOUR_USERNAME\AppData\Roaming\pyinstaller
   ```

3. **Rebuild from scratch:**
   ```bash
   pyinstaller --clean build_config\causa_agent.spec
   ```

## ✅ Verify the Fix

After rebuilding, the new executable should:
1. Launch without console window
2. NOT crash with AttributeError
3. Open the Streamlit interface in browser
4. Work normally

## 🔍 Troubleshooting

If still seeing the error after rebuild:

1. **Check you're running the right exe:**
   ```bash
   # Check file modification time
   dir dist\CAUSA-Agent.exe
   ```
   The date/time should be AFTER you made the fixes

2. **Verify source files have the fix:**
   Open `src/launcher.py` and check lines 22-32 have the safety checks

3. **Check PyInstaller is using correct source:**
   Look at the build output - it should show it's packaging files from your `src/` directory

4. **Force clean rebuild:**
   ```bash
   pyinstaller --clean --noconfirm --onefile build_config\causa_agent.spec
   ```

## 📝 Build Command Summary

From the project root (`C:\...\agipro_agent\`):

```bash
# Clean everything
rmdir /s /q build dist
del *.spec

# Rebuild
pyinstaller --clean build_config\causa_agent.spec

# Run the new executable
dist\CAUSA-Agent.exe
```

## ⚡ Quick Test

After rebuild, test immediately:
1. Double-click the new `dist/CAUSA-Agent.exe`
2. Should NOT show any console error
3. Should open browser with Streamlit app

---

**Remember:** The code is fixed, you just need to rebuild the executable with the fixed code!
