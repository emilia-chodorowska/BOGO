// Rolki BOGO z Instagrama doTERRA Europe: `ego-browser nodejs < rolki.mjs`
// Bez logowania profil pokazuje 12 najnowszych rolek — wystarcza, bo doTERRA wrzuca je ok. 3 dni przed startem.
// Wypisuje linki do rolek, w których opisie jest „BOGO”; pobieranie: yt-dlp (komenda w /bogo).
const task = await taskSpace("BOGO - rolki doTERRA na Instagramie");
const page = task.page("p1");
const znalezione = [];
for (const konto of ["doterraeurope"]) {
  await page.goto(`https://www.instagram.com/${konto}/reels/`);
  await page.waitForTimeout(5000);
  const ids = await page.evaluate(() =>
    [...new Set([...document.querySelectorAll('a[href*="/reel/"]')].map((a) => a.href.match(/\/reel\/([^/]+)/)[1]))]);
  for (const id of ids) {
    await page.goto(`https://www.instagram.com/reel/${id}/`);
    await page.waitForTimeout(2500);
    const opis = await page.evaluate(() => document.querySelector('meta[property="og:description"]')?.content || "");
    if (/bogo/i.test(opis)) znalezione.push({ url: `https://www.instagram.com/reel/${id}/`, opis: opis.replace(/\s+/g, " ").slice(0, 160) });
  }
}
await task.finish({ keep: [] });
console.log(JSON.stringify(znalezione, null, 1));
