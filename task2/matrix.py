import random


# *–––––––––––––––––––––––→
# |                       x
# |
# |     25  24  23  22  21
# |     10  9   8   7   20
# |     11  2   1   6   19
# |     12  3   4   5   18
# |     13  14  15  16  17
# |
# ↓ y


class Matrix:
    def __init__(self, n):
        self.k = 2 * n - 1

        self.value = [[random.randint(1, self.k ** 2) for _ in range(self.k)]
                      for _ in range(self.k)]

    def print(self):
        for row in self.value:
            print('\t'.join(map(str, row)))

    def print_by_spiral(self):
        x, y = self.k // 2, self.k // 2

        self.print_el(x, y)

        for side_elements_count in range(2, self.k + 1, 2):
            # Начинаем круг
            x -= 1
            self.print_el(x, y)
            # 1) side_elements_count - 1 елементов вниз:
            for _ in range(side_elements_count - 1):
                y += 1
                self.print_el(x, y)

            # 2) side_elements_count елементов вправо
            for _ in range(side_elements_count):
                x += 1
                self.print_el(x, y)

            # и т.д.
            for _ in range(side_elements_count):
                y -= 1
                self.print_el(x, y)

            for _ in range(side_elements_count):
                x -= 1
                self.print_el(x, y)

        print()

    def print_el(self, x, y):
        print(self.value[y][x], end=' ')


if __name__ == '__main__':
    m = Matrix(4)
    m.print()
    print('\n\n')
    m.print_by_spiral()
