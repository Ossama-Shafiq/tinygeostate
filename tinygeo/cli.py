from tinygeo.geometry import GeometryState


def main():
    geo = GeometryState()

    print("TinyGeoState v0.1")
    print("Commands:")
    print("  point NAME X Y")
    print("  line NAME P1 P2")
    print("  distance A B")
    print("  angle A B C")
    print("  orientation A B C")
    print("  parallel L1 L2")
    print("  perpendicular L1 L2")
    print("  show")
    print("  quit")
    print()

    while True:
        try:
            raw = input("tinygeo> ").strip()

            if not raw:
                continue

            parts = raw.split()
            command = parts[0].lower()

            if command == "quit":
                print("Goodbye.")
                break

            elif command == "point":
                _, name, x, y = parts
                result = geo.create_point(name, float(x), float(y))
                print(result)

            elif command == "line":
                _, name, p1, p2 = parts
                result = geo.create_line(name, p1, p2)
                print(result)

            elif command == "distance":
                _, a, b = parts
                print(geo.distance(a, b))

            elif command == "angle":
                _, a, b, c = parts
                print(geo.angle(a, b, c))

            elif command == "orientation":
                _, a, b, c = parts
                print(geo.orientation(a, b, c))

            elif command == "parallel":
                _, l1, l2 = parts
                print(geo.parallel(l1, l2))

            elif command == "perpendicular":
                _, l1, l2 = parts
                print(geo.perpendicular(l1, l2))

            elif command == "show":
                print(geo.snapshot())

            else:
                print(f"Unknown command: {command}")

        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
