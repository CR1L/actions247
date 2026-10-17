import sys
from playwright.sync_api import sync_playwright
B="http://127.0.0.1:8247/"
shots=[("index.html","fr","home_fr.png"),("index.html","en","home_en.png"),("actif/tslax.html","fr","asset_tslax_fr.png"),("actif/nvdaon.html","fr","asset_nvdaon_fr.png")]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for path,lang,out in shots:
        pg=b.new_page(viewport={"width":1366,"height":900})
        errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)))
        pg.goto(B+"index.html"); pg.evaluate(f"localStorage.setItem('a247lang','{lang}')")
        pg.goto(B+path, wait_until="networkidle")
        pg.screenshot(path="screenshots/"+out, full_page=True)
        print(out, "errors:", errs, "rows:", pg.locator("#t tbody tr").count() if "index" in path else "-")
    b.close()
