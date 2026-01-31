
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aims_exam.settings')
django.setup()

from django.utils import translation
from django.urls import translate_url

def test_i18n():
    print("--- I18N Testing Script ---")
    print(f"Languages: {settings.LANGUAGES}")
    print(f"Locale Paths: {settings.LOCALE_PATHS}")
    print(f"Use I18N: {settings.USE_I18N}")
    
    # Check if translation works
    print("\n[Testing Russian Translation]")
    translation.activate('ru')
    print(f"Active Language: {translation.get_language()}")
    txt = translation.gettext("Dashboard")
    print(f"Dashboard -> {txt}")
    if txt == "Dashboard":
        print("FAIL: Russian translation not found/loaded")
    else:
        print("SUCCESS: Russian translation loaded")

    print("\n[Testing Kyrgyz Translation]")
    translation.activate('ky')
    print(f"Active Language: {translation.get_language()}")
    txt = translation.gettext("Dashboard")
    print(f"Dashboard -> {txt}")
    if txt == "Dashboard":
        print("FAIL: Kyrgyz translation not found/loaded")
    else:
        print("SUCCESS: Kyrgyz translation loaded")
        
    print("\n[Testing URL Translation]")
    path = '/ru/schools/' # Assuming this exists
    print(f"Original Path: {path}")
    
    from django.urls import resolve, reverse
    try:
        match = resolve(path)
        print(f"Resolved View: {match.view_name}")
        print(f"Resolved Args: {match.args}")
        print(f"Resolved Kwargs: {match.kwargs}")
        
        # Test Reversing to 'ky'
        with translation.override('ky'):
            rev_path = reverse(match.view_name, args=match.args, kwargs=match.kwargs)
            print(f"Reversed in 'ky': {rev_path}")
            
        with translation.override('en'):
            rev_path_en = reverse(match.view_name, args=match.args, kwargs=match.kwargs)
            print(f"Reversed in 'en': {rev_path_en}")

    except Exception as e:
        print(f"Resolution/Reverse Error: {e}")

    new_path_ky = translate_url(path, 'ky')
    print(f"translate_url result: {new_path_ky}")

    if new_path_ky == path and 'ru' in path: 
         print("FAIL: translate_url failed to change language prefix")
    else:
         print("SUCCESS: translate_url changed prefix")

if __name__ == "__main__":
    test_i18n()
