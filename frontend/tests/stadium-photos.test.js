import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';

const photos = JSON.parse(readFileSync(new URL('../src/utils/stadiumPhotos.json', import.meta.url)));
const sources = JSON.parse(readFileSync(new URL('../public/images/stadiums/sources.json', import.meta.url)));
const credits = readFileSync(new URL('../public/images/stadiums/credits.html', import.meta.url), 'utf8');
const normalize = (name) => name.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\./g, '').replace(/\s+/g, ' ').trim();
const clubs = new Map();
for (const [key, photo] of Object.entries(photos)) {
  for (const alias of photo.aliases) {
    const normalized = normalize(alias);
    assert.ok(!clubs.has(normalized) || clubs.get(normalized).key === key, `Ambiguous club alias: ${alias}`);
    clubs.set(normalized, { ...photo, key });
  }
}
const club = (name) => clubs.get(normalize(name));

test('every mapped ground has a local JPEG and complete attribution', () => {
  for (const [key, photo] of Object.entries(photos)) {
    const source = sources[key];
    assert.ok(source?.author && source?.license && source?.licenseUrl && source?.source, key);
    assert.ok(source.source.startsWith('https://commons.wikimedia.org/wiki/File:'), key);
    assert.ok(existsSync(new URL(`../public${photo.image}`, import.meta.url)), key);
    const bytes = readFileSync(new URL(`../public${photo.image}`, import.meta.url));
    assert.equal(bytes[0], 0xff, key);
    assert.equal(bytes[1], 0xd8, key);
    assert.ok(credits.includes(`id="${key}"`), key);
  }
});

test('similarly named clubs and changed grounds remain distinct', () => {
  assert.notEqual(club('FC Barcelona').image, club('Barcelona SC').image);
  assert.notEqual(club('CD Nacional').image, club('Club Nacional de Football').image);
  assert.notEqual(club('Coventry City FC').image, club('Birmingham City FC').image);
  assert.match(club('Coventry City FC').stadium, /Coventry/);
  assert.equal(club('CA Mineiro').stadium, 'Arena MRV');
  assert.equal(club('Italy'), undefined);
  assert.equal(club('Unknown FC'), undefined);
});
