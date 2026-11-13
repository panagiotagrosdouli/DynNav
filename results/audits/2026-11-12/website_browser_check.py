import json
from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000}); errors=[]; routes=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 for route in ['/']+['/contributions/C%02d.html'%i for i in range(1,27)]:
  response=page.goto('http://127.0.0.1:3001'+route)
  routes.append({'route':route,'status':response.status})
  assert response.ok, routes[-1]
 page.set_viewport_size({'width':390,'height':844})
 page.goto('http://127.0.0.1:3001/')
 page.screenshot(path='work/audit/website-mobile.png',full_page=True)
 overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
 page.keyboard.press('Tab')
 focused=page.evaluate('document.activeElement.tagName')
 assert not errors,errors
 Path('work/audit/website-browser-results.json').write_text(json.dumps({'routes':routes,'page_errors':errors,'mobile_horizontal_overflow':overflow,'first_tab_element':focused,'scope':'route loads, page errors, one mobile viewport and initial keyboard focus only; not complete accessibility compliance'},indent=2))
 browser.close()
