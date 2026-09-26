// Run against the local server with:
// playwright-cli run-code --filename=tests/browser-check.js
async page => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const check = (value, message) => { if (!value) throw new Error(message); };
  const text = id => page.locator(`#${id}`).textContent();
  const scrub = value => page.locator('#timeline').evaluate((input, v) => {
    input.value = String(v);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }, value);

  await page.setViewportSize({width:1440,height:1100});
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto('http://127.0.0.1:8000');
  await page.waitForFunction(() => !document.querySelector('#year').disabled);
  check(await page.locator('#year option').count() === 100, '100 selectable years');
  check(await page.locator('.event-button').count() === 2, '2026 has two eclipses');
  check(await text('play-label') === '暂停', 'automatic playback');
  await page.waitForFunction(() => Number(document.querySelector('#timeline').value) > 1);
  await page.locator('#play').click();
  const paused = await text('current-time');
  await page.waitForTimeout(150);
  check(await text('current-time') === paused, 'pause freezes clock');

  await page.locator('.contact').filter({hasText:'食甚'}).click();
  check(await text('current-time') === '19:33:37', '2026 greatest eclipse in UT+8');
  check(await text('phase-name') === '食甚', 'greatest phase');
  await page.waitForTimeout(220);
  await page.screenshot({path:'output/playwright/desktop.png',fullPage:true});
  const maximum = await page.locator('#moon').evaluate(canvas => canvas.toDataURL());
  await scrub(100);
  const initial = await page.locator('#moon').evaluate(canvas => canvas.toDataURL());
  check(maximum !== initial, 'moon rendering changes with time');
  await page.locator('#timezone').selectOption('0');
  await page.locator('.contact').filter({hasText:'食甚'}).click();
  check(await text('current-time') === '11:33:37', 'world-time conversion');

  await page.locator('.event-button').nth(1).click();
  check(await page.locator('.contact').count() === 5, 'partial event has five contacts');
  check((await text('total-duration')).trim() === '—', 'partial event has no totality');
  await page.locator('#year').selectOption('2002');
  check(await page.locator('.event-button').count() === 3, '2002 has three eclipses');
  check(await page.locator('.contact').count() === 3, 'penumbral event has three contacts');
  await page.locator('#year').selectOption('2001');
  check(await page.locator('#previous-year').isDisabled(), 'lower year boundary');
  await page.locator('#year').selectOption('2100');
  check(await page.locator('#next-year').isDisabled(), 'upper year boundary');

  // 2001-01-09 UT greatest falls on January 10 in UT+8.
  await page.locator('#year').selectOption('2001');
  await page.locator('#timezone').selectOption('8');
  await page.locator('.contact').filter({hasText:'食甚'}).click();
  check(await text('current-date') === '2001.01.10', 'cross-midnight display date');
  await page.locator('#timezone').selectOption('0');
  check(await text('current-date') === '2001.01.09', 'UT date follows offset');

  await page.locator('#year').selectOption('2026');
  await page.locator('#timezone').selectOption('8');
  await page.locator('.contact').filter({hasText:'食甚'}).click();
  await page.waitForTimeout(220);
  const layouts = [];
  for (const width of [1440,1024,768,375]) {
    await page.setViewportSize({width,height:1000});
    const size = await page.evaluate(() => ({width:innerWidth,content:document.documentElement.scrollWidth}));
    check(size.content <= size.width, `no page overflow at ${width}px`);
    layouts.push(size);
    if (width===375) await page.screenshot({path:'output/playwright/mobile.png',fullPage:true});
  }
  await page.locator('#timeline').focus();
  await page.keyboard.press('ArrowRight');
  check(Number(await page.locator('#timeline').inputValue()) > 500, 'keyboard scrubbing');

  await page.locator('#speed').selectOption('4');
  await scrub(999);
  await page.locator('#play').click();
  await page.waitForFunction(() => document.querySelector('#play-label').textContent === '再看一次');
  check(await text('phase-name') === '半影食终', 'playback stops at the final contact');
  await page.locator('#replay').click();
  check(Number(await page.locator('#timeline').inputValue()) < 100, 'replay resets progress');
  check((await text('playback-status')).includes('15 秒'), 'speed updates playback duration');

  await page.emulateMedia({reducedMotion:'reduce'});
  await page.reload();
  await page.waitForFunction(() => !document.querySelector('#year').disabled);
  check(await text('play-label') === '播放', 'reduced-motion starts paused');
  await page.context().setOffline(true);
  await page.locator('#year').selectOption('2025');
  await page.locator('.contact').filter({hasText:'食甚'}).click();
  check((await text('current-date')).startsWith('2025'), 'offline event switching');
  await page.context().setOffline(false);
  check(errors.length === 0, `no JavaScript errors: ${errors.join('; ')}`);

  // A missing catalogue has a clear retry affordance.
  await page.route('**/eclipses.json', route => route.fulfill({status:503,body:'Unavailable'}));
  await page.reload();
  await page.locator('#load-error').waitFor({state:'visible'});
  check(await page.locator('#play').isDisabled(), 'loading error disables playback');
  check(await page.locator('#load-error button').textContent() === '重新加载', 'retry control');
  await page.unroute('**/eclipses.json');
  await page.locator('#load-error button').click();
  await page.waitForFunction(() => !document.querySelector('#year').disabled);
  await page.setViewportSize({width:1440,height:1100});
  await page.locator('.contact').filter({hasText:'食甚'}).click();
  return {result:'PASS',checks:'play, pause, replay, end, speed, years, all eclipse types, contacts, clock, midnight, keyboard, reduced motion, offline, error/retry',layouts,errors};
}
