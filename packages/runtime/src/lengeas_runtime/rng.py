"""Small PCG XSL-RR 128/64 generator with caller-supplied 128-bit seed."""

from __future__ import annotations

from dataclasses import dataclass

from packages.runtime.src.lengeas_runtime.errors import RuntimeErrorCode

MASK_64 = (1 << 64) - 1
MASK_128 = (1 << 128) - 1
MULTIPLIER = 47026247687942121848144207491837523525


@dataclass(slots=True)
class PCG64:
    state: int
    increment: int

    @classmethod
    def from_seed(cls, seed: int) -> PCG64:
        if not 0 <= seed <= MASK_128:
            raise RuntimeErrorCode("seed_invalid")
        mixed = (seed | 0x9E3779B97F4A7C15) - (seed & 0x9E3779B97F4A7C15)
        generator = cls(0, ((mixed << 1) | 1) & MASK_128)
        generator.next_u64()
        generator.state = (generator.state + seed) & MASK_128
        generator.next_u64()
        return generator

    def next_u64(self) -> int:
        previous = self.state
        self.state = (previous * MULTIPLIER + self.increment) & MASK_128
        high = previous >> 64
        low = previous & MASK_64
        shifted = (high | low) - (high & low)
        rotation = previous >> 122
        return ((shifted >> rotation) | (shifted << ((-rotation) & 63))) & MASK_64

    def randbelow(self, upper: int) -> int:
        if upper <= 0 or upper > 2**64:
            raise RuntimeErrorCode("random_bound_invalid")
        threshold = (2**64 - upper) % upper
        while True:
            value = self.next_u64()
            if value >= threshold:
                return value % upper
