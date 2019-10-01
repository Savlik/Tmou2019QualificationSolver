import asyncio
import re

import aiohttp
import tqdm
import unidecode

WORDS_URL = "https://cgit.freedesktop.org/libreoffice/dictionaries/tree/cs_CZ/cs_CZ.dic"
CHECK_URL = "https://tmou.honzamrazek.cz/?puzzle={}&solution={}"
# puzzle number and expected length of solution
PUZZLES = (
    [11, 8],
    [12, 9],
    [13, 5],
    [14, 10],
    [21, 7],
    [22, None],
    [23, 8],
    [31, 5],
    [32, None],
    [41, None],
    [51, None]
)


async def fetch_words():
    async with aiohttp.request("GET", WORDS_URL) as response:
        content = await response.text(encoding="latin2")
        lines = unidecode.unidecode(content).split("\n")
        words = {None: set()}
        for line in lines:
            m = re.match(r"^(.*)/.*(H|Z|M|P|D|C).*$", line)
            if m:
                word = m.group(1).lower()
                words[None].add(word)
                length = len(word)
                if length not in words:
                    words[length] = set()
                words[length].add(word)
        return words


async def solve_puzzle(number, length, words, tq):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for word in words[length]:
            tasks.append(asyncio.create_task(process(number, word, session, tq)))
        for task in tasks:
            await task


async def process(number, word, session, tq):
    async with session.get(CHECK_URL.format(number, word)) as response:
        if "správně! Odešlete řešení" in await response.text():
            tq.write("{}: {}".format(number, word))
    tq.update()


async def main():
    words = await fetch_words()

    tq = tqdm.tqdm()
    for puzzle in PUZZLES:
        await solve_puzzle(*puzzle, words, tq)


if __name__ == "__main__":
    asyncio.run(main())
