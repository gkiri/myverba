#!/usr/bin/env python3
"""
Test script to verify that all import issues have been resolved.
This script tests the imports that were causing failures.
"""

import sys
import os

def test_openai_import():
    """Test OpenAI import that was failing"""
    try:
        from openai import OpenAI
        print("✅ OpenAI import successful")
        return True
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False

def test_manim_components():
    """Test manim component imports"""
    try:
        # Test basic manim import first
        import manim
        print("✅ Manim import successful")
        
        # Test manim-voiceover import 
        from manim_voiceover import VoiceoverScene
        from manim_voiceover.services.openai import OpenAIService
        print("✅ Manim-voiceover imports successful")
        
        return True
    except ImportError as e:
        print(f"❌ Manim component import failed: {e}")
        return False

def test_project_drishti_components():
    """Test Project Drishti component imports"""
    try:
        # Add the project path to sys.path to ensure imports work
        project_path = os.path.dirname(os.path.abspath(__file__))
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
            
        from goldenverba.final_manim.anim_gemini.project_drishti import config
        print("✅ Project Drishti config import successful")
        
        from goldenverba.final_manim.anim_gemini.project_drishti.didactic_scripter import DidacticScripter
        print("✅ DidacticScripter import successful")
        
        from goldenverba.final_manim.anim_gemini.project_drishti.visual_architect import VisualArchitect
        print("✅ VisualArchitect import successful")
        
        from goldenverba.final_manim.anim_gemini.project_drishti.manim_renderer import ManimRenderer
        print("✅ ManimRenderer import successful")
        
        from goldenverba.final_manim.anim_gemini.project_drishti.video_analyzer import VideoAnalyzer
        print("✅ VideoAnalyzer import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Project Drishti component import failed: {e}")
        return False

def test_verba_components():
    """Test Verba component imports"""
    try:
        # Test the embedder that was using text2vec-palm
        from goldenverba.components.embedding.GoogleEmbedder import GoogleEmbedder
        embedder = GoogleEmbedder()
        if embedder.vectorizer == "none":
            print("✅ GoogleEmbedder vectorizer correctly updated to 'none'")
        else:
            print(f"⚠️  GoogleEmbedder vectorizer is '{embedder.vectorizer}', expected 'none'")
        
        return True
    except ImportError as e:
        print(f"❌ Verba component import failed: {e}")
        return False

def main():
    """Run all import tests"""
    print("🧪 Testing imports after dependency fixes...\n")
    
    tests = [
        ("OpenAI Import", test_openai_import),
        ("Manim Components", test_manim_components),
        ("Project Drishti Components", test_project_drishti_components),
        ("Verba Components", test_verba_components),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"🔍 Testing {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("=" * 40)
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All imports working correctly!")
        return 0
    else:
        print("⚠️  Some imports still failing. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 