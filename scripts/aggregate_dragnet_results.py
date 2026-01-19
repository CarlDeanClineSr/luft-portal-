import json
import argparse
import glob
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    all_results = []
    for f in glob.glob(f"{args.input_dir}/**/*.json", recursive=True):
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                if 'results' in data:
                    all_results.extend(data['results'])
        except Exception as e:
            print(f"Warning: Failed to load {f}: {e}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'total_scanned': len(all_results), 'results': all_results}, f, indent=2)
    
    print(f"Aggregated {len(all_results)} results into {args.output}")

if __name__ == '__main__':
    main()
