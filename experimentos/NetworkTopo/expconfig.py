def parse_connectivity(file):
    with open(file, "r") as f:
        content = [l.strip() for l in f.readlines() if "->" in l]
    return set(content)