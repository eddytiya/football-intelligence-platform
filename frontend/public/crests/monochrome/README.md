# Broadcast crest assets

White-only SVG paths with transparent backgrounds and interior cutouts. No raster images, external references, scripts, CSS filters or generated lettering.

Source credit: **FootyLogos.com**. Original SVG geometry is retained in the base files. For Madrid, United and Barcelona, the `-outline.svg` files preserve filled lettering/detail and selectively open broad fields along their vector boundaries. They do not indiscriminately outline every letter. Other reviewed monochrome files retain their sourced geometry. Club marks belong to their respective owners; these are sourced/adapted assets, not official assets authored by this project or exact reproductions of the AI-generated study.

| Club | Local file | Source |
| --- | --- | --- |
| Real Madrid | `real-madrid-outline.svg` | https://www.footylogos.com/logos/real-madrid-monochrome |
| Manchester United | `manchester-united-outline.svg` | https://www.footylogos.com/logos/manchester-united-monochrome |
| FC Barcelona | `fc-barcelona-outline.svg` | https://www.footylogos.com/logos/fc-barcelona-monochrome |
| Arsenal | `arsenal-outline.svg` | https://www.footylogos.com/logos/arsenal-monochrome |
| Manchester City | `manchester-city-outline.svg` | https://www.footylogos.com/logos/manchester-city-monochrome |
| Newcastle United | `newcastle-united-outline.svg` | https://www.footylogos.com/logos/newcastle-united-monochrome |
| Bayern Munich | `bayern-munich-outline.svg` | https://www.footylogos.com/logos/bayern-munich-monochrome |
| Juventus | `juventus-outline.svg` | https://www.footylogos.com/logos/juventus-monochrome |

Use these on dark matchup surfaces with `ClubCrest` and `variant="broadcast"`. Dashboard featured fixtures and the match-centre scoreboard use that variant. Small dashboard lists retain their original colour crests. Unknown teams fall back to their supplied original crest, rather than borrowing another club's badge or creating a white silhouette. Add reviewed SVGs and explicit aliases in `src/utils/clubCrests.js` to expand coverage.

The three-club preview is `/crests/preview.html`. Assets are loaded locally; there are no subscriptions, paid services or runtime requests to the source site. Coverage is eight clubs. All others deliberately retain their supplied original crest; failed or absent sources render a text fallback.

The development-only curator is `.impeccable/curate_broadcast_vectors.py`. It uses exact source path groups for the three adaptations and preserves their lettering. The initial installer alone produces the earlier all-contour variants; run the curator last when rebuilding these assets. Do not rasterize an AI sample or apply a grayscale filter to create new club files.
