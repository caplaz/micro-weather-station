#!/usr/bin/env python3
"""Translation validation script for micro weather station integration."""

import json
from pathlib import Path


def validate_translations():
    """Validate that all translation files have consistent structure."""
    translations_dir = Path("custom_components/micro_weather/translations")

    # Load English as reference
    en_file = translations_dir / "en.json"
    with open(en_file, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    # Get all translation files
    translation_files = list(translations_dir.glob("*.json"))

    print(f"🌍 Found {len(translation_files)} translation files:")

    errors = []

    for file_path in sorted(translation_files):
        lang = file_path.stem
        print(f"  📄 {lang}.json", end="")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check structure consistency
            if not check_structure(en_data, data, lang):
                errors.append(f"{lang}: Structure mismatch")
                print(" ❌")
            else:
                print(" ✅")

        except json.JSONDecodeError as e:
            errors.append(f"{lang}: JSON decode error - {e}")
            print(" ❌ JSON Error")
        except Exception as e:
            errors.append(f"{lang}: Error - {e}")
            print(" ❌ Error")

    if errors:
        print(f"\n❌ Validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print("\n✅ All translations valid!")
        return True


def check_structure(reference, target, lang):
    """Check if target structure matches reference structure."""

    def check_keys(ref_dict, target_dict, path=""):
        if not isinstance(ref_dict, dict) or not isinstance(target_dict, dict):
            return True

        ref_keys = set(ref_dict.keys())
        target_keys = set(target_dict.keys())

        if ref_keys != target_keys:
            missing = ref_keys - target_keys
            extra = target_keys - ref_keys
            if missing:
                print(f"\n    Missing keys in {lang}{path}: {missing}")
            if extra:
                print(f"\n    Extra keys in {lang}{path}: {extra}")
            return False

        for key in ref_keys:
            if isinstance(ref_dict[key], dict):
                if not check_keys(ref_dict[key], target_dict[key], f"{path}.{key}"):
                    return False

        return True

    return check_keys(reference, target)


def show_language_coverage():
    """Show which languages are supported."""
    translations_dir = Path("custom_components/micro_weather/translations")

    languages = {
        "en": "English",
        "it": "Italian (Italiano)",
        "de": "German (Deutsch)",
        "es": "Spanish (Español)",
        "fr": "French (Français)",
    }

    print("\n🌍 Supported Languages:")
    for file_path in sorted(translations_dir.glob("*.json")):
        lang_code = file_path.stem
        lang_name = languages.get(lang_code, f"Unknown ({lang_code})")
        print(f"  🏴 {lang_code}: {lang_name}")


if __name__ == "__main__":
    print("🔍 Validating micro weather station translations...")
    print("=" * 50)

    valid = validate_translations()
    show_language_coverage()

    if valid:
        print("\n🎉 Translation validation successful!")
        exit(0)
    else:
        print("\n💥 Translation validation failed!")
        exit(1)
