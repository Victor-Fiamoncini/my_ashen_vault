"""Usage: python -m ashen_vault [--map NAME] [--at TX,TZ,YAW] [--smoke FRAMES] [--shot PATH] [--script STEPS]"""
import argparse
import os
import sys


def main(argv=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)  # so `data` (dialogue) imports from a source checkout
    ap = argparse.ArgumentParser(prog="ashen_vault", description="Ashen Vault")
    ap.add_argument("--map", help="Skip the title and start on this map")
    ap.add_argument("--at", help="Start tile and heading in degrees: TX,TZ,YAW")
    ap.add_argument("--smoke", type=int, help="Run this many frames, save a screenshot, exit")
    ap.add_argument("--shot", help="Screenshot path for --smoke")
    ap.add_argument("--script", help="Scripted input, e.g. 'forward:1.5 attack wait:1'")
    args = ap.parse_args(argv)

    from ashen_vault.game import Game
    Game(vars(args)).run()


if __name__ == "__main__":
    main()
