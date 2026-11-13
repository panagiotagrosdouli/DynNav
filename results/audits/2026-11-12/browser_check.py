import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('work/audit')
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000})
 errors=[]; responses=[]
 page.on('pageerror',lambda error:errors.append(str(error)))
 page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}) if ':8000/' in r.url else None)
 page.goto('http://127.0.0.1:3000')
 page.get_by_role('textbox',name='Research request',exact=True).fill('Compare all four planners over 1 deterministic seed and generate a reproducible report.')
 page.get_by_role('button',name='Compile protocol',exact=True).click()
 run=page.get_by_role('button',name='Run 4 planner executions',exact=True)
 run.wait_for(timeout=20000)
 run.click()
 page.get_by_text('Executed evidence',exact=True).first.wait_for(timeout=60000)
 page.screenshot(path=str(out/'workspace-executed.png'),full_page=True)
 assert not errors,errors
 assert any(r['status']==202 for r in responses), responses
 assert not [r for r in responses if r['status']>=400],responses
 (out/'browser-results.json').write_text(json.dumps({'status':'passed','story':'compile protocol -> execute 4 planners -> display executed evidence','page_errors':errors,'api_responses':responses},indent=2))
 browser.close()
