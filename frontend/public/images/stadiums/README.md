# Home-ground photographs

## Wikimedia Commons API sync

No API key or environment variable is needed. From `frontend`, run:

```sh
npm run stadiums:sync -- --check  # Verify reviewed files and licensing without writing
npm run stadiums:sync           # Fetch metadata, download missing photos, rebuild mapping and credits
npm run stadiums:sync -- --refresh # Also replace existing photo bytes
```

The script calls Commons Imageinfo in small sequential batches with a descriptive User-Agent and timeouts. Existing photos remain cached locally so match cards do not call Wikimedia on every visit. API errors stop the sync before downloads are committed. Author attribution is preserved from the reviewed source records; the linked Commons page supplies full attribution. To expand coverage, add a reviewed stadium, exact club aliases, local image path and Commons file source with attribution to `sources.json`, then sync. Search hits are not automatically accepted as the correct ground.

The reviewed catalog covers home grounds across Europe and South America. `coverage.json` records the latest photo count, coverage of the local team database (including historical duplicate team records), and unresolved teams. Shared grounds use one photo with multiple exact club aliases. These are actual stadium images, including archival and exterior views; they are not live feeds or proof of a fixture's venue.

`credits.html` supplies visible author, licence, source, photo-date and CSS presentation credits. `sources.json` preserves source metadata and download URLs alongside the JPEGs. Original pixels are retained; the interface applies object-fit cropping and a dark CSS overlay.

The client uses a smaller mapping at `frontend/src/utils/stadiumPhotos.json` and exact aliases in `stadiumPhotos.js`. Unknown home clubs and load failures show a neutral surface. Never infer a venue from the away club or substitute another ground. Other page backgrounds are outside this feature's scope.

Preparation: `.impeccable/prepare_stadium_assets.py` in the repository root. Its input records and Commons metadata are kept under `.impeccable/stadium-candidates/`. Candidate search hits alone are not trusted; selected photographs and corresponding stadium identities were checked before use. Everton uses Hill Dickinson Stadium rather than Goodison Park. FC Barcelona's Camp Nou photo is archival, explicitly dated in the credits.

## Reviewing another ground

1. Confirm the club's ground using the stadium article and club information. Resolve outdated provider names, former grounds, temporary moves, and shared grounds before assigning a photo. A national team's most recently supplied venue is not a permanent home-ground mapping.
2. Open the Commons file page and inspect the photo itself. Reject logos, diagrams, portraits, unrelated grounds and ambiguous search hits. Prefer a landscape photograph at least 800 pixels wide.
3. Record the photographer, exact licence, licence link, original file page, photo date when supplied, and the source used to confirm the ground. This importer supports JPEG photos under CC BY, CC BY-SA, CC0 or public-domain terms.
4. Add exact club aliases to `sources.json`. Do not assign a short name used by a different club. Run the sync and open `credits.html` to inspect the resulting photo and attribution.
5. Run `node --test tests/stadium-photos.test.js` from `frontend` to check local images, attribution anchors and known club/ground distinctions.

The October 2026 expansion keeps cached article extracts, candidate metadata, visual review sheets and explicit review approvals under `.impeccable/stadium-candidates/`. Entries that could not be verified, lacked suitable photos, or were refused by the image server remain unresolved instead of borrowing another club's ground.
