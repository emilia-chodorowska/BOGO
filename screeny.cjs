// Screeny kart zestawów (widok telefonu, 402 px × 3) i pakietu (układ 700 px × 2) z index.html, index-eur.html i index-en.html.
// Uruchomienie: node screeny.cjs <folder-wyjściowy>   → <folder>/PLN/*.png, <folder>/EUR/*.png i <folder>/EN/*.png i <folder>/DE/*.png (EUR po angielsku / niemiecku)
const path = require('path');
const fs = require('fs');
const puppeteer = require('/opt/homebrew/lib/node_modules/decktape/node_modules/puppeteer-core');

const OUT = path.resolve(process.argv[2] || 'screeny');
const STRONY = { PLN: 'index.html', EUR: 'index-eur.html', EN: 'index-en.html', DE: 'index-de.html' };

const slug = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l')
  .replace(/[™]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

(async () => {
  const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new' });
  for (const [waluta, plik] of Object.entries(STRONY)) {
    const dir = path.join(OUT, waluta);
    fs.mkdirSync(dir, { recursive: true });
    const url = 'file://' + path.join(__dirname, plik);
    const p = await b.newPage();

    // karty zestawów: telefon
    await p.setViewport({ width: 402, height: 874, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
    await p.goto(url, { waitUntil: 'networkidle0' });
    await p.evaluate(() => document.fonts.ready);
    const karty = await p.evaluate(() => [...document.querySelectorAll('article')].map(a => {
      const q = a.getBoundingClientRect();
      return { x: q.x, y: q.y + scrollY, w: q.width, h: q.height, tytul: a.querySelector('h3').innerText };
    }));
    for (const [i, k] of karty.entries()) {
      const nazwa = `zestaw-${i + 1}-${slug(k.tytul.split("+")[0])}.png`;
      await p.screenshot({ path: path.join(dir, nazwa), clip: { x: Math.max(0, k.x - 20), y: k.y - 12, width: Math.min(402, k.w + 40), height: k.h + 24 }, captureBeyondViewport: true });
    }

    // pakiet: szerszy układ (kafle w rzędzie, gratis ze zdjęciem z lewej), wyższa ramka zdjęcia
    await p.setViewport({ width: 700, height: 900, deviceScaleFactor: 2 });
    await p.goto(url, { waitUntil: 'networkidle0' });
    await p.evaluate(() => document.fonts.ready);
    const bx = await p.evaluate(() => {
      const img = document.querySelector('img[alt^="Pakiet BOGO"], img[alt^="BOGO bundle"], img[alt^="BOGO-Paket"]');
      img.parentElement.style.height = '300px';
      const q = img.closest('div[style*="border-radius:22px"]').getBoundingClientRect();
      return { x: q.x, y: q.y + scrollY, w: q.width, h: q.height };
    });
    await p.screenshot({ path: path.join(dir, 'pakiet-bogo.png'), clip: { x: bx.x - 20, y: bx.y - 20, width: bx.w + 40, height: bx.h + 40 }, captureBeyondViewport: true });
    await p.close();
    console.log(`${waluta}: ${karty.length} kart + pakiet → ${dir}`);
  }
  await b.close();
})();
