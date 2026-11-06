"""How hash quality changes a Bloom filter's false-positive rate.

A Bloom filter with m bits and k hash functions holds n items. With ideal hashing the false-positive rate (FPR)
is (1 - e^(-kn/m))^k. Here m=10,000, k=7, n=2,000, so the ideal FPR is 0.1378. Four flawed hash families each break
one property: collision rate, independence, uniform distribution, and the avalanche effect.
"""
import hashlib
import json
import math
import random
import string
import sys

M, K, N_INSERT, N_QUERY = 10_000, 7, 2_000, 20_000
ALPHABET = (string.ascii_letters + string.digits).encode()


def rand_string(n=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n)).encode()


def sha256_int(b: bytes) -> int:
    return int(hashlib.sha256(b).hexdigest(), 16)


class BloomFilter:
    def __init__(self, m, k, hash_family):
        self.m, self.k, self.hash_family = m, k, hash_family
        self.bits = [0] * m

    def positions(self, key):
        return [self.hash_family(i, key) % self.m for i in range(self.k)]

    def add(self, key):
        for p in self.positions(key):
            self.bits[p] = 1

    def contains(self, key):
        return all(self.bits[p] for p in self.positions(key))

    def occupancy(self):
        return sum(self.bits) / self.m


def theoretical_fpr(m, k, n):
    return (1 - math.e ** (-k * n / m)) ** k


# ---- hash families -------------------------------------------------------------------------------
def good_hash(i, key):  # SHA-256 of (index, key): independent, uniform, strong avalanche
    return sha256_int(i.to_bytes(4, "big") + key)


def high_collision_hash(i, key):  # keeps only 12 bits, so at most 4,096 distinct values
    return sha256_int(i.to_bytes(4, "big") + key) & 0xFFF


def dependent_hash(i, key):  # all k positions are one base hash plus a fixed offset: not independent
    return sha256_int(b"base" + key) + i * 13


def make_bad_distribution_hash(m):  # only ever touches the first quarter of the bit array
    return lambda i, key: sha256_int(i.to_bytes(4, "big") + key) % (m // 4)


def poor_avalanche_hash(i, key):  # byte-sum based: a one-character change barely moves the output
    s = sum(key) + i * 257
    s ^= (s << 7) & 0xFFFFFFFF
    s ^= s >> 3
    return s & 0x7FFFFFFF


# ---- data ----------------------------------------------------------------------------------------
def make_insert_set(n):
    seen, out = set(), []
    while len(out) < n:
        x = rand_string()
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def make_random_queries(inserted, n):
    s, out = set(inserted), []
    while len(out) < n:
        q = rand_string()
        if q not in s:
            out.append(q)
    return out


def make_near_queries(inserted, n):
    """Queries that differ from an inserted key by exactly one character."""
    out, L, idx = [], len(inserted[0]), 0
    while len(out) < n:
        base = bytearray(inserted[idx % len(inserted)])
        base[random.randrange(L)] = random.choice(ALPHABET)
        y = bytes(base)
        if y != inserted[idx % len(inserted)]:
            out.append(y)
        idx += 1
    return out


def run(m, k, inserted, queries, hash_family):
    bf = BloomFilter(m, k, hash_family)
    for x in inserted:
        bf.add(x)
    return sum(bf.contains(q) for q in queries) / len(queries), bf.occupancy()


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    random.seed(seed)
    inserted = make_insert_set(N_INSERT)
    rand_q, near_q = make_random_queries(inserted, N_QUERY), make_near_queries(inserted, N_QUERY)
    experiments = [
        ("(a) collision rate", "good", good_hash, rand_q), ("(a) collision rate", "high-collision", high_collision_hash, rand_q),
        ("(b) independence", "dependent", dependent_hash, rand_q),
        ("(c) distribution", "biased", make_bad_distribution_hash(M), rand_q),
        ("(d) avalanche", "good (near queries)", good_hash, near_q), ("(d) avalanche", "poor avalanche", poor_avalanche_hash, near_q),
    ]
    results = []
    print(f"seed {seed}  ideal FPR {theoretical_fpr(M, K, N_INSERT):.4f}")
    for prop, name, fam, qs in experiments:
        fpr, occ = run(M, K, inserted, qs, fam)
        results.append(dict(property=prop, hash=name, fpr=round(fpr, 5), occupancy=round(occ, 4)))
        print(f"{prop:20s} {name:22s} FPR {fpr:.4f}  occupancy {occ:.3f}")
    json.dump(results, open("results/results_seed%d.json" % seed, "w"), indent=2)
