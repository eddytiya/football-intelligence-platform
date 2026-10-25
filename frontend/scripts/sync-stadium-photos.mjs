// Refresh reviewed Commons photos without an API key or browser-time requests.
import { readFile, writeFile, access, rename } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const folder = path.join(root, 'public/images/stadiums');
const sourcesFile = path.join(folder, 'sources.json');
const check = process.argv.includes('--check');
const refresh = process.argv.includes('--refresh');
const sources = JSON.parse(await readFile(sourcesFile, 'utf8'));
const headers = { 'User-Agent': 'FootballIntelligencePlatform/1.0 (stadium photo attribution sync)' };
const escape = (text) => String(text ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// Preserve author-specified attribution already reviewed in sources.json.
const plain = (text) => String(text ?? '').replace(/<[^>]*>/g, '').trim();
const pause = (milliseconds = 6000) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function get(url) {
  for (let attempt = 0; attempt < 4; attempt++) {
    const response = await fetch(url, { headers, signal: AbortSignal.timeout(30000) });
    if ([429, 503].includes(response.status) && attempt < 3) {
      const retry = response.headers.get('retry-after');
      const seconds = /^\d+$/.test(retry || '') ? Number(retry) : (Date.parse(retry || '') - Date.now()) / 1000;
      const delay = Math.max(10, Number.isFinite(seconds) ? seconds : 15 * (attempt + 1));
      if (delay > 60) throw new Error(`Wikimedia requests a ${Math.ceil(delay)} second cooldown; run sync later`);
      console.log(`Wikimedia cooldown: waiting ${Math.ceil(delay)} seconds`);
      await response.body?.cancel();
      await pause(Math.ceil(delay) * 1000);
      continue;
    }
    if (!response.ok) throw new Error(`Wikimedia HTTP ${response.status}; retry later if rate limited`);
    return response;
  }
}

const updated = structuredClone(sources);
const downloads = [];
const entries = Object.entries(sources);
for (let offset = 0; offset < entries.length; offset += 4) {
  const batch = entries.slice(offset, offset + 4);
  const titles = batch.map(([, record]) => {
    const url = new URL(record.source);
    if (url.hostname !== 'commons.wikimedia.org' || !url.pathname.startsWith('/wiki/File:')) throw new Error('Expected a reviewed Commons file page');
    return decodeURIComponent(url.pathname.slice('/wiki/'.length)).replaceAll('_', ' ');
  });
  const params = new URLSearchParams({ action: 'query', format: 'json', formatversion: '2',
    titles: titles.join('|'), prop: 'imageinfo', iiprop: 'url|size|mime|extmetadata',
    iiurlwidth: '1280', iiextmetadatafilter: 'Artist|LicenseShortName|LicenseUrl' });
  const data = await (await get(`https://commons.wikimedia.org/w/api.php?${params}`)).json();
  if (data.error) throw new Error(`Commons: ${data.error.code}`);
  for (let index = 0; index < batch.length; index++) {
    const [key, record] = batch[index];
    const info = data.query?.pages?.find((page) => page.title === titles[index])?.imageinfo?.[0];
    const meta = info?.extmetadata;
    const license = plain(meta?.LicenseShortName?.value);
    const licenseUrl = meta?.LicenseUrl?.value || (license === 'Public domain' ? 'https://creativecommons.org/publicdomain/mark/1.0/' : null);
    if (!info || info.mime !== 'image/jpeg' || info.width < 800 || info.width < info.height
      || !/^(CC BY(?:-SA)?\b|CC0\b|Public domain\b)/i.test(license)
      || !/^https?:\/\//.test(licenseUrl || '') || !meta.Artist?.value) {
      throw new Error(`${key}: missing image or unsupported license/dimensions; existing assets retained`);
    }
    // Small originals can otherwise produce a non-standard, clamped thumbnail
    // size which Wikimedia's CDN refuses to generate.
    const download = info.width <= 1280 ? info.url : info.thumburl || info.url;
    if (!['upload.wikimedia.org', 'thumb.wikimedia.org'].includes(new URL(download).hostname)) throw new Error('Unexpected image host');
    const target = path.join(folder, `${key}.jpg`);
    if (!/^[a-z0-9-]+$/.test(key) || record.image !== `/images/stadiums/${key}.jpg`) throw new Error('Invalid stadium image path');
    const exists = await access(target).then(() => true, () => false);
    updated[key] = { ...record, download };
    // Do not replace the displayed photo's attribution until its bytes are refreshed.
    if (!check && (refresh || !exists)) {
      await pause();
      const response = await get(download);
      if (!response.headers.get('content-type')?.startsWith('image/jpeg')) throw new Error(`${key}: expected JPEG`);
      const image = Buffer.from(await response.arrayBuffer());
      if (image.length > 5_000_000 || image[0] !== 255 || image[1] !== 216) throw new Error(`${key}: invalid or oversized image`);
      // Stage in memory until all API responses and downloads have validated.
      downloads.push({ target, image });
      updated[key] = { ...record, download, license, licenseUrl };
    }
    console.log(`${key}: ${check ? 'API verified' : refresh || !exists ? 'downloaded' : 'cached'} (${license})`);
  }
  await pause();
}

if (!check) {
  for (const { target, image } of downloads) {
    await writeFile(`${target}.tmp`, image);
    await rename(`${target}.tmp`, target);
  }
  const cards = Object.entries(updated).map(([key, record]) => `<article id="${escape(key)}"><img loading="lazy" src="${escape(key)}.jpg" alt="${escape(record.stadium)}"><h2>${escape(record.stadium)}</h2><p>${escape(record.aliases.slice(0, 2).join(', '))}</p><p>Photo: ${escape(record.author)} · <a href="${escape(record.licenseUrl)}">${escape(record.license)}</a></p><p>${escape(record.photoDate)}</p><p><a href="${escape(record.source)}">Original photo and full attribution</a></p><p>${escape(record.changes)}</p></article>`);
  await writeFile(sourcesFile, `${JSON.stringify(updated, null, 2)}\n`);
  const manifest = Object.fromEntries(Object.entries(updated).map(([key, { stadium, aliases, image }]) => [key, { stadium, aliases, image }]));
  await writeFile(path.join(root, 'src/utils/stadiumPhotos.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  const creditsFile = path.join(folder, 'credits.html');
  const credits = await readFile(creditsFile, 'utf8');
  await writeFile(creditsFile, credits.replace(/<main>[\s\S]*?<\/main>/, `<main>${cards.join('')}</main>`));
}
console.log(`${entries.length} stadium sources ${check ? 'verified; no files changed' : 'synced'}. No API key required.`);
