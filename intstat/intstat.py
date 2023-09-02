#!/usr/bin/env python3

import argparse
import time
import shutil

from dataclasses import dataclass
from typing import List


@dataclass
class IRQEntry(object):
    irq: str
    desc: str
    cpus: List[str]
    ints: List[int]


def read_proc():
    with open("/proc/interrupts", mode="r", encoding="utf-8") as fd:
        entries = []
        cpu_names = [x for x in fd.readline().strip().split(" ") if x]
        for raw_line in [x for x in fd.readlines() if x]:
            fields = [x for x in raw_line.strip().split(" ") if x]
            irq = fields[0].rstrip(":").strip()
            desc = " ".join(fields[len(cpu_names) + 1 :])
            ints = (
                [int(fields[1])]
                if irq in ["MIS", "ERR"]
                else [int(x) for x in fields[1 : len(cpu_names) + 1]]
            )
            entries.append(IRQEntry(irq, desc, cpu_names, ints))
        return entries


def range_list(x):
    if not x:
        return []
    rc = []
    for part in x.split(","):
        if "-" in part:
            a, b = part.split("-")
            a, b = int(a), int(b)
            rc.extend(range(a, b + 1))
        else:
            a = int(part)
            rc.append(a)
    return rc


def diff(old, new):
    entries = []
    for x in range(len(old)):
        lhs, rhs = old[x], new[x]
        if lhs.irq != rhs.irq or lhs.ints != rhs.ints:
            entries.append(rhs)
    return entries


def print_rows(rows, args):
    cpuset = range_list(args.cpus)
    if args.non_trivial:
        for i in range(len(rows[0].cpus)):
            s = 0
            for x in rows:
                if x.irq.isnumeric():
                    s += x.ints[i]
            if s != 0:
                cpuset.append(i)
    if cpuset:
        for x in rows:
            x.cpus = [x.cpus[i] for i in cpuset]
            x.ints = [x.ints[i] for i in cpuset]

    width = (
        max(len(str(max(sum([x.ints for x in rows], [])))), len(rows[0].cpus[-1])) + 1
    )
    fmt = "{:3} | " + " ".join(
        [("{:>" + str(width) + "}").format(i) for i in rows[0].cpus]
    )
    print(fmt.format(""))
    for x in rows:
        if sum(x.ints) != 0 or args.zero:
            fmt = "{:3} | " + " ".join(
                [("{:" + str(width) + "}").format(i) for i in x.ints]
            )
            if args.desc:
                fmt += " " + x.desc
            print(fmt.format(x.irq))


def main(args):
    if args.show:
        print_rows(read_proc(), args)
        return

    while True:
        now = read_proc()
        time.sleep(args.time)
        print_rows(diff(now, read_proc()), args)
        print("=" * shutil.get_terminal_size().columns)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="intstat", description="Linux interrupts stats"
    )
    parser.add_argument(
        "-t", "--time", default=3, help="The interval of printing, in seconds"
    )
    parser.add_argument("-s", "--show", action="store_true", help="Show current stats")
    parser.add_argument("-z", "--zero", action="store_true", help="Show zero stats")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument(
        "-c", "--cpus", default="", help="CPU masks, begins at 0. eg: '1-2,4'"
    )
    parser.add_argument(
        "-d", "--desc", action="store_true", help="Show the description of IRQ"
    )
    parser.add_argument(
        "-n",
        "--non-trivial",
        action="store_true",
        help="Ignore CPUs without any interrupts.",
    )
    main(parser.parse_args())
