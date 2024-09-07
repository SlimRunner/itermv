class RadixCounter:
    def __init__(self, radix: int, start=0) -> None:
        if radix < 1:
            raise ValueError("radix cannot be negative")
        self.__radix = radix
        self.__counter = [0]
        self.setCount(start)

    def setCount(self, num: int):
        self.__counter = [num]
        while self.__counter[0] >= self.__radix:
            self.__counter.insert(0, self.__counter[0] // self.__radix)
            self.__counter[1] %= self.__radix
        if len(self.__counter) > 1 and self.__counter[0] == 0:
            self.__counter.pop(0)
        return self

    def increase(self):
        pos = len(self.__counter) - 1
        self.__counter[pos] += 1
        while self.__counter[pos] >= self.__radix:
            carry = self.__counter[pos] // self.__radix
            out = self.__counter[pos] % self.__radix
            self.__counter[pos] = out
            pos -= 1
            if pos < 0:
                if carry > 0:
                    self.__counter.insert(0, carry)
                # assuming delta is +1
                break
            else:
                self.__counter[pos] += carry
        return self

    def str(self, upper=False) -> str:
        offset = (65 if upper else 97) - 10
        if self.__radix > 36:
            raise IndexError(
                f"Not enough letters in alphabet for radix of {self.__radix}"
            )
        return "".join([chr(i + (offset if i > 9 else 48)) for i in self.__counter])

    def raw(self) -> list[int]:
        return self.__counter[:]


class AlphaCounter:
    def __init__(self, start=0) -> None:
        self.__radix = 26
        self.__counter = [0]
        self.setCount(start)

    def setCount(self, num: int):
        radix = self.__radix
        self.__counter = [num]
        while self.__counter[0] >= radix:
            self.__counter.insert(0, self.__counter[0] // radix - 1)
            self.__counter[1] %= radix
        return self

    def increase(self):
        radix = self.__radix
        pos = len(self.__counter) - 1
        self.__counter[pos] += 1
        while self.__counter[pos] >= radix:
            carry = self.__counter[pos] // radix
            out = self.__counter[pos] % radix
            self.__counter[pos] = out
            pos -= 1
            if pos < 0:
                if carry >= 0:
                    self.__counter.insert(0, carry - 1)
                break
            else:
                self.__counter[pos] += carry
        return self

    def str(self, upper=False) -> str:
        offset = 65 if upper else 97
        return "".join([chr(n + offset) for i, n in enumerate(self.__counter)])

    def raw(self) -> list[int]:
        return self.__counter[:]
