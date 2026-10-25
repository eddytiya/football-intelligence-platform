import photos from "./stadiumPhotos.json";

const normalise = (name) =>
  String(name || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\./g, "")
    .replace(/\s+/g, " ")
    .trim();
const byClub = new Map(
  Object.entries(photos).flatMap(([key, photo]) =>
    photo.aliases.map((alias) => [normalise(alias), { ...photo, key }]),
  ),
);

// Exact reviewed club aliases only. Never infer from a substring or the away club.
export function stadiumPhotoFor(homeTeamName) {
  return byClub.get(normalise(homeTeamName)) || null;
}
