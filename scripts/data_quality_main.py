#!/usr/bin/env python3
"""🚀 ChainGuardian Data Quality Dashboard - FIXED"""
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def run_script(script_name):
    """Run script safely."""
    try:
        result = subprocess.run(
            ["poetry", "run", "python", f"scripts/data_quality/{script_name}"],
            capture_output=True, text=True, timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings:", result.stderr)
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")

def show_menu():
    print("\n" + "="*60)
    print("🎯 CHAINGUARDIAN DATA QUALITY DASHBOARD")
    print("="*60)
    print("1. 📊 Full Quality Report v2 (Ground Truth)")
    print("2. 🏷️  Check Ground Truth Labels") 
    print("3. 🧹 Database Cleanup (Duplicates)")
    print("4. 🔍 Export ML Dataset")
    print("5. 📈 Quick Status")
    print("0. Exit")
    
    return input("\nChoose: ")

def main():
    while True:
        choice = show_menu()
        if choice == '1':
            run_script("data_quality_report_v2.py")
        elif choice == '2':
            run_script("check_ground_truth_labels.py")
        elif choice == '3':
            run_script("database_quality_control.py")
        elif choice == '4':
            print("💾 ML dataset already exported: data/ml_final_train_dataset.csv")
        elif choice == '5':
            subprocess.run(["poetry", "run", "python", "scripts/status_check.py"])
        elif choice == '0':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
