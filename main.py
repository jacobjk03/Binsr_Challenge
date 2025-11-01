"""
Main entry point for TREC Inspection Report Generator
Generates both output_pdf.pdf (TREC report) and bonus_pdf.pdf (creative report)
"""

import sys
import os
from datetime import datetime
from generate_trec_report import TRECReportGenerator
from generate_bonus_pdf import BonusPDFGenerator


def check_requirements():
    """Check if required files exist"""
    errors = []
    
    # Check for inspection.json
    if not os.path.exists('inspection.json'):
        errors.append("❌ inspection.json not found")
    else:
        print("✓ Found inspection.json")
    
    # Check for template
    if not os.path.exists('TREC_Template_Blank.pdf'):
        errors.append("❌ TREC_Template_Blank.pdf not found")
    else:
        print("✓ Found TREC_Template_Blank.pdf")
    
    return errors


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("         TREC INSPECTION REPORT GENERATOR - v1.0")
    print("="*70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check requirements
    print("Checking requirements...")
    errors = check_requirements()
    
    if errors:
        print("\n❌ ERRORS FOUND:")
        for error in errors:
            print(f"   {error}")
        print("\nPlease ensure all required files are present.")
        return 1
    
    print("\n" + "-"*70)
    
    # Generate main TREC report
    try:
        print("\n🔵 GENERATING MAIN TREC REPORT (output_pdf.pdf)")
        print("-"*70)
        
        trec_generator = TRECReportGenerator(
            json_path='inspection.json',
            template_path='TREC_Template_Blank.pdf'
        )
        trec_generator.generate_report('output_pdf.pdf')
        
        # Verify output
        if os.path.exists('output_pdf.pdf'):
            size = os.path.getsize('output_pdf.pdf') / 1024  # KB
            print(f"\n✅ Main report generated successfully!")
            print(f"   File: output_pdf.pdf ({size:.1f} KB)")
        else:
            print("\n❌ Failed to generate output_pdf.pdf")
            return 1
        
    except Exception as e:
        print(f"\n❌ Error generating TREC report: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "-"*70)
    
    # Generate bonus PDF
    try:
        print("\n🟢 GENERATING BONUS REPORT (bonus_pdf.pdf)")
        print("-"*70)
        
        bonus_generator = BonusPDFGenerator(json_path='inspection.json')
        bonus_generator.generate_report('bonus_pdf.pdf')
        
        # Verify output
        if os.path.exists('bonus_pdf.pdf'):
            size = os.path.getsize('bonus_pdf.pdf') / 1024  # KB
            print(f"\n✅ Bonus report generated successfully!")
            print(f"   File: bonus_pdf.pdf ({size:.1f} KB)")
        else:
            print("\n❌ Failed to generate bonus_pdf.pdf")
            return 1
        
    except Exception as e:
        print(f"\n❌ Error generating bonus report: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Final summary
    print("\n" + "="*70)
    print("                     ✅ ALL REPORTS GENERATED!")
    print("="*70)
    print("\nOutput files:")
    print("  1. output_pdf.pdf  - Main TREC inspection report")
    print("  2. bonus_pdf.pdf   - Creative executive summary report")
    print("\n" + "="*70)
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

