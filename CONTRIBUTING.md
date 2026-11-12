# Contributing to Ashen Vault

Thanks for wanting to help! Bug reports, fixes, new enemies, maps, spells, tests and documentation
are all welcome.

## Ground rules

- **Original content only.** Ashen Vault is inspired by FromSoftware's *King's Field*, but nothing in
  it may come from that series or any other existing game: no names, maps, characters, story, art,
  music or sounds. New art and audio should be generated in code like the rest of the game.
- **No asset files in the game.** Textures, models and sounds are procedural
  (`src/ashen_vault/render/texture_gen.py`, `render/models.py`, `audio/synth.py`).
- **Be kind.** Assume good faith in issues and reviews.

## Getting set up

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/). Using [mise](https://mise.jdx.dev)?
`mise install` picks up the pinned Python and uv versions.

```sh
git clone <this repository's URL> my_ashen_vault
cd my_ashen_vault
uv sync                 # creates .venv with the game and the dev tools
uv run ashen-vault      # play
```

Read [`AGENTS.md`](AGENTS.md) for the project layout, conventions and debug flags. It's written for AI
coding agents but is the most complete developer guide, so it's worth reading if you code by hand too.

## Making a change

1. **Open an issue first** for anything bigger than a small fix, so we can agree on the approach.
2. **Branch from `development`**, not `master`. `master` only moves when a release is cut.
3. **Keep game logic out of raylib.** Code in `world/`, `player/`, `ai/` and `save/` must not import
   raylib, and new logic there should come with tests in `tests/`.
4. **Run the checks** before pushing. This is what CI runs:

   ```sh
   mise run check          # or, without mise:
   uv run ruff check && uv run ruff format --check && uv run pytest --cov
   ```

5. **Try it in the game** if you touched rendering, UI, audio or anything that runs per frame. A smoke
   run is the quickest way, and a screenshot in the PR helps a lot:

   ```sh
   ASHEN_VAULT_SAVE=/tmp/test_save.json \
     uv run ashen-vault --map sunken_keep --at 15,22,0 --smoke 30 --script "wait:0.3 cast" --shot shot.png
   ```

   Setting `ASHEN_VAULT_SAVE` keeps test runs away from your real save file.

6. **Open a pull request against `development`.** Describe what changed and why, and how you tested it.

### Style

- `ruff format` decides formatting; `ruff check --fix` fixes most lint findings.
- Use `util.rround` instead of `round` in game math (the numbers depend on round-half-away-from-zero).
- Don't reformat `.map` files: their grids are whitespace-sensitive.
- Add dependencies with `uv add` / `uv add --dev` so `uv.lock` stays in sync.
- Write commit messages in the imperative mood ("Add frost spell", not "Added frost spell").

## Sign your commits (DCO)

Every commit must carry a `Signed-off-by` line, certifying that you wrote the change or otherwise
have the right to submit it under the project's license, as described in the
[Developer Certificate of Origin](https://developercertificate.org/). Git adds the line for you:

```sh
git commit -s -m "Add frost spell"
```

Forgot? `git commit --amend -s` fixes the last commit, and `git rebase --signoff development` fixes a
whole branch.

## License

Ashen Vault is licensed under the [GNU General Public License v3.0 or later](LICENSE). By contributing
you agree that your contributions are licensed under the same terms. You keep the copyright on your
own work.
