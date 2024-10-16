from typing import Iterator


def generate_gradient(color1: tuple[int, int, int], color2: tuple[int, int, int], n: int) -> (
        Iterator)[tuple[int, int, int]]:
    for i in range(n):
        r = color1[0] + (color2[0] - color1[0]) * i / (n - 1)
        g = color1[1] + (color2[1] - color1[1]) * i / (n - 1)
        b = color1[2] + (color2[2] - color1[2]) * i / (n - 1)
        yield int(r), int(g), int(b)