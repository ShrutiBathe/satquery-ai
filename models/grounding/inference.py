from pathlib import Path
from pprint import pprint

from .grounding import run_grounding


def main():

    image_path = Path("models/grounding/satellite_test.jpg")

    queries = [
        "large building",
        "residential building",
        "industrial building",
        "warehouse",
        "roads",
        "vehicles",
        "ships",
        "airplanes",
        "water",
        "trees",
    ]

    for query in queries:

        print("\n" + "=" * 50)
        print(f"Testing: {query}")
        print("=" * 50)

        result = run_grounding(
            image_path=str(image_path),
            query=query,
        )

        print(f"Detections: {result['statistics']['num_detections']}")

        for detection in result["detections"]:
            print(
                f"  {detection['label']} | "
                f"confidence={detection['confidence']} | "
                f"box={detection['box']}"
            )


if __name__ == "__main__":
    main()