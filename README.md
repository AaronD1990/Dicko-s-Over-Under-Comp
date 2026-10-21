# Over Under Comp: setup guide

This folder is the whole website. It has three parts:

- `index.html` is the page your friends see.
- `data/seasons.json` holds every season's lines and picks (2026-27 is the live one).
- `data/standings.json` holds each team's current record. A script rewrites it every 2 hours during the season.

Everything below uses free tiers (GitHub Pages and GitHub Actions). Menu names on GitHub can change, so if a step looks different, look for the closest match.

## One-time setup (about 10 minutes)

1. Create a free account at github.com (you do this yourself, with your own email and password).
2. Create a new repository. Name it whatever you like, for example `over-under`. Make it Public (free GitHub Pages needs a public repository, as far as I know).
3. Upload everything in this folder to the repository, keeping the folder structure. The hidden `.github` folder must go up too, because it contains the daily updater. If dragging folders onto the web page skips it, use the "Add file" > "Upload files" option again for that folder, or ask me for help with GitHub Desktop.
4. Turn on the website: Settings > Pages > under "Build and deployment" choose "Deploy from a branch", pick the `main` branch and the `/ (root)` folder, then Save. After a minute or two GitHub shows your link, which looks like `https://YOURNAME.github.io/over-under/`.
5. Turn on the updater: open the Actions tab, accept the prompt to enable workflows if shown, pick "Update standings" and press "Run workflow" once.
6. Open your link. Within a couple of minutes of that first run the board should show real records.

Send the link to your friends. That is all they need.

## How it behaves

- The page checks for new standings every 10 minutes while it is open.
- The updater only saves a file when a record has changed, so you will see a commit after game days.
- If the updater ever fails (ESPN down, odd data), it writes nothing and the site keeps the last good standings. The failed run shows a red cross on the Actions tab.
- Until the season is finished the leaderboard says "on track". Once every team has played 82 games it switches to "correct".

## Next season

Add a new season object to `data/seasons.json` (id, the player names, each team's line and picks, plus `"live": true`), turn the old season's `live` off and add a `final` win total to each of its teams, then change `SEASON_ID` and `ESPN_SEASON` at the top of `scripts/update_standings.py`. Or just send me the new spreadsheet and I will do it.

## Changing a pick or a line

Edit `data/seasons.json` on GitHub (pencil icon) and commit. Picks are written as O or U, with a `$` after the letter for a sure thing, for example `"U$"`.
