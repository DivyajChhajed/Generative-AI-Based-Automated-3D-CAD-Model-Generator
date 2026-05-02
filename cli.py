"""
CLI entry point for the API 6A CAD Generator.

Usage:
    python cli.py                         # Interactive prompt mode
    python cli.py --list                  # Show all supported sizes
    python cli.py --prompt "bonnet 3-1/16 10k"  # Direct generation
"""

import argparse
import sys

from main import generate_from_prompt, list_supported, find_closest_match, extract_request, load_dimensions


def main():
    parser = argparse.ArgumentParser(
        description="API 6A CAD Model Generator - Generate STEP files from natural language prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python cli.py --prompt "Generate API 6A bonnet 3-1/16 10k PSI"\n'
            '  python cli.py --prompt "flange 2-1/16 5000"\n'
            "  python cli.py --list\n"
            "  python cli.py           # interactive mode\n"
        ),
    )
    parser.add_argument("--prompt", type=str, help="Natural language prompt for part generation")
    parser.add_argument("--list", action="store_true", help="Show all supported (part, size, pressure) combos")

    args = parser.parse_args()

    if args.list:
        df = list_supported()
        print("\n--- Supported Configurations ---")
        print(df.to_string(index=False))
        print(f"\nTotal: {len(df)} configurations\n")
        return

    prompt = args.prompt
    if not prompt:
        prompt = input("Enter prompt (bonnet / flange / spool): ").strip()

    if not prompt:
        print("Error: No prompt provided.")
        sys.exit(1)

    try:
        out = generate_from_prompt(prompt)
        print(f"[SUCCESS] STEP created: {out}")
    except ValueError as e:
        error_msg = str(e)
        print(f"[ERROR] {error_msg}")

        # If it's a "no exact match" error, offer closest alternatives
        if "Closest available" in error_msg:
            choice = input("\nWould you like to try the closest match? (y/n): ").strip().lower()
            if choice == "y":
                try:
                    part, size_inch, pressure_psi = extract_request(prompt)
                    suggestions = find_closest_match(part, size_inch, pressure_psi)
                    if suggestions:
                        best = suggestions[0]
                        print(f"\nUsing: {best['part']} {best['size']}\" @ {best['pressure']} PSI")
                        dims = load_dimensions(best["part"], best["size"], best["pressure"])
                        from main import build_model, export_step, unique_step_name, OUT_DIR
                        model = build_model(best["part"], dims)
                        out_name = unique_step_name(best["part"], best["size"], best["pressure"])
                        out_path = export_step(model, OUT_DIR / out_name)
                        print(f"[SUCCESS] STEP created: {out_path}")
                    else:
                        print("No suggestions available.")
                except Exception as e2:
                    print(f"[ERROR] Failed to generate closest match: {e2}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
