"""
Bihar School Games - Student Registration auto-filler (Playwright)

Setup (ek baar):
    pip install playwright
    playwright install chromium

Run:
    python register_students.py

Pehli baar DRY_RUN = True rakhiye: form bharega, par Register nahi dabayega.
Sab theek lage tab DRY_RUN = False kar dijiye.
"""
import csv
import os
import re
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://www.biharsportsmashaal.in/school/login"
URL = "https://www.biharsportsmashaal.in/pages/register-student"
CSV_FILE = "students.csv"
IMAGE_DIR = "images"    # Drive se download ki hui images yahan rakhein
DRY_RUN = True          # True = Register button nahi dabayega
PROFILE_DIR = "pw_profile"  # login session yahan save hoga

OPEN_FORM_BUTTON = "Register New Student"   # portal ka neela button jo form kholta hai
SINGLE_TAB = False          # True = saare students ek hi tab mein (agar naye tab mein login/form nahi milta)

# ---- Video recording (verify karne aur error dekhne ke liye) ----
RECORD_VIDEO = True         # True = har student ki alag video VIDEO_DIR mein
VIDEO_QUALITY = "720p"      # "720p" (1280x720) ya "1080p" (1920x1080; bade monitor par hi)
VIDEO_DIR = "videos"        # DHYAN: video mein Aadhaar, bank details aur photos dikhte hain. Kaam ke baad delete karein
SIZES = {"720p": {"width": 1280, "height": 720}, "1080p": {"width": 1920, "height": 1080}}


# ---------- data check (galat data se pehle hi rok dega) ----------
def validate(s):
    if re.search(r"[eE]\+\d", s["aadhaar"] + s["account_number"] + s["mobile"]):
        return ["Aadhaar/account number scientific notation (E+) mein hai: CSV Excel mein khuli ya save hui lagti hai. "
                "Teacher panel se batch zip dobara download karke fresh students.csv use karein (Excel mein na kholein)"]
    errs = []
    if not re.fullmatch(r"\d{12}", s["aadhaar"]):
        errs.append("Aadhaar 12 digit ka hona chahiye")
    if not re.fullmatch(r"\d{10}", s["mobile"]):
        errs.append("Mobile 10 digit ka hona chahiye")
    if not re.fullmatch(r"[A-Za-z]{4}0[A-Za-z0-9]{6}", s["ifsc"]):
        errs.append("IFSC code galat format mein hai")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s["dob"]):
        errs.append("DOB dd/mm/yyyy format mein likhiye")
    names = {s["student_name"].lower(), s["mother_name"].lower(), s["father_name"].lower()}
    if s["beneficiary_name"].lower() not in names:
        errs.append("Beneficiary name student/mother/father ke naam se match karna chahiye")
    for key in ("photo", "aadhaar_front", "aadhaar_back"):
        path = s[key]
        if not os.path.isfile(path):
            errs.append(f"{key} file nahi mili: {path}")
        elif os.path.getsize(path) > 200 * 1024:
            errs.append(f"{key} 200KB se badi hai: {path}")
    return errs


def scroll_modal_to(page, box):
    """Modal ke andar ka scroll container dhundhkar box tak scroll karta hai aur video ke liye ruk jata hai."""
    box.evaluate("""e => {
        let p = e.parentElement;
        while (p) {
            if (p.scrollHeight > p.clientHeight + 5 && getComputedStyle(p).overflowY !== 'visible') {
                const r = e.getBoundingClientRect(), pr = p.getBoundingClientRect();
                p.scrollTo({top: p.scrollTop + (r.top - pr.top) - 120, behavior: 'smooth'});
                break;
            }
            p = p.parentElement;
        }
    }""")
    page.wait_for_timeout(1500)


def upload(page, label, path):
    """File input us box se dhoondhta hai jiske andar `label` likha hai (number se nahi),
    kyunki upload ke baad portal inputs hata deta hai aur number badal jate hain."""
    box = page.get_by_text(label, exact=True).first
    box.wait_for(state="visible", timeout=10000)
    try:
        scroll_modal_to(page, box)            # modal ka apna scroll, video mein upload wala hissa dikhe
    except Exception:
        pass
    inp = box.locator("xpath=ancestor::*[.//input[@type='file']][1]").locator("input[type=file]")
    if inp.count() != 1:
        raise RuntimeError(f"'{label}' wale box mein {inp.count()} file input mile (1 hona chahiye)")
    inp.set_input_files(path)
    page.wait_for_timeout(1500)                        # video mein preview dikhe
    try:
        box.wait_for(state="detached", timeout=15000)   # upload accept hone par box badal jata hai
    except Exception:
        raise RuntimeError(f"'{label}': upload ke baad box nahi badla, shayad portal ne image accept nahi ki")
    page.wait_for_timeout(1000)


def select_game(page, game):
    """Game dropdown keyboard se kholkar chunta hai (mouse click par depend nahi). Enter tabhi dabata hai jab
    menu khula ho aur option focus mein ho (warna Enter poora form submit kar deta)."""
    gi = page.locator("input[id^='react-select-'][id$='-input']").first
    opts = page.locator("[id^='react-select-'][id*='-option-']")
    gi.focus()
    gi.press("ArrowDown")
    try:
        opts.first.wait_for(state="visible", timeout=5000)
    except Exception:
        try:
            gi.click(timeout=3000)
            opts.first.wait_for(state="visible", timeout=3000)
        except Exception:
            raise RuntimeError("Game dropdown mein koi option nahi aaya. Shayad Age/Category ya gender ke hisaab se options nahi bane")
    texts = [x.strip() for x in opts.all_inner_texts()]
    want = game.strip().lower()
    idx = next((i for i, x in enumerate(texts) if x.lower() == want), None)
    if idx is None:
        idx = next((i for i, x in enumerate(texts) if want in x.lower()), None)
    if idx is None:
        raise RuntimeError(f"Game '{game}' options mein nahi mila. Portal ke options: {texts}")
    for _ in range(idx):                       # ArrowDown ke baad pehla option focus mein hota hai
        gi.press("ArrowDown")
    gi.press("Enter")
    if not page.locator("input[name=gameName]").input_value():
        raise RuntimeError(f"Game '{game}' chunne ke baad bhi select nahi hua")


# ---------- ek student ka form bharna ----------
def fill_student(page, s):
    page.wait_for_selector("#formStudentName", timeout=10000)
    # Portal ka accessibility widget poori screen par 40% kala parda (z=999999) lagata hai: video dhundhla aur mouse click block.
    page.add_style_tag(content="#accessibility-overlay{display:none !important}")

    page.fill("#formStudentName", s["student_name"])

    is_girl = s["gender"].strip().lower() in ("girl", "female", "f")
    page.locator("#genderFemale" if is_girl else "#genderMale").check(force=True)

    page.fill("#formAadharNumber", s["aadhaar"])

    # DOB: poori date EK saath daalte hain (fill). Akshar-akshar type karne par portal har adhoori date
    # (jaise "0" -> 01/01/2000) par "age restriction" error dikhata hai aur form dhundhla ho jata hai (video se pakda gaya).
    dob = page.locator('input[placeholder="dd/mm/yyyy"]')
    age_js = "() => { const e = document.querySelector('#formAgeAsOn'); return !!e && e.value.trim() !== ''; }"
    dob.fill(s["dob"])
    page.keyboard.press("Tab")
    try:
        page.wait_for_function(age_js, timeout=8000)
    except Exception:
        dob.fill("")                                   # doosri koshish: bahut tez type karke
        dob.press_sequentially(s["dob"], delay=0)
        page.keyboard.press("Tab")
        try:
            page.wait_for_function(age_js, timeout=8000)
        except Exception:
            err = page.locator("text=/age restriction/i")
            msg = err.first.inner_text().strip() if err.count() else ""
            raise RuntimeError(f"DOB '{dob.input_value()}' ke baad Age nahi bhari. Portal ka message: {msg or '(koi nahi)'}. "
                               "Portal mein yahi DOB haath se type karke dekhein")

    portal_cat = page.input_value("#formCategory")
    if s.get("category") and s["category"] not in portal_cat:
        print(f"   WARNING: hamari category {s['category']!r}, portal ne {portal_cat!r} dikhayi. Eligible games alag ho sakte hain")

    page.fill("#formMotherName", s["mother_name"])
    page.fill("#formFatherName", s["father_name"])
    page.fill("#formMobileNumber", s["mobile"])
    if s.get("email"):
        page.fill("#formEmail", s["email"])

    select_game(page, s["game"])

    page.fill("#formAccountHolderName", s["beneficiary_name"])
    page.fill("#formAccountNumber", s["account_number"])
    page.fill("#formIfscCode", s["ifsc"].upper())

    # Uploads: label se box dhoondhte hain (order wahi: photo, front, back)
    upload(page, "Upload Student Photo", s["photo"])
    upload(page, "Upload Front Side", s["aadhaar_front"])
    upload(page, "Upload Back Side", s["aadhaar_back"])

    age = page.input_value("#formAgeAsOn")
    cat = page.input_value("#formCategory")
    game_val = page.locator("input[name=gameName]").input_value()
    print(f"   Age: {age!r} | Category: {cat!r} | Game value: {game_val!r}")
    if not game_val:
        raise RuntimeError("Game select nahi hua")


def describe_overlay(page):
    """Screen ke beech mein upar-upar kaun se element hain: dhundhle parde ka pata lagane ke liye."""
    try:
        return page.evaluate(r"""() => document.elementsFromPoint(window.innerWidth / 2, window.innerHeight / 2).slice(0, 8).map(e => {
            const cs = getComputedStyle(e);
            return `${e.tagName.toLowerCase()}#${e.id}.${String(e.className).slice(0, 70)} pos=${cs.position} z=${cs.zIndex} bg=${cs.backgroundColor} opacity=${cs.opacity} text="${(e.innerText || '').slice(0, 40).replace(/\n/g, ' ')}"`;
        })""")
    except Exception as e:
        return [f"describe_overlay fail: {e}"]


def capture_proof(page, i, s):
    """Form upar se neeche tak scroll karke 3 screenshot: fields, uploads, neeche (Register button). Video mein bhi dikhta hai."""
    base = f"proof/{i:03d}_{re.sub(r'[^A-Za-z0-9]+', '_', s['student_name']).strip('_')}"

    def shot(tag, scroll_js=None, target=None):
        try:
            if target is not None:
                target.evaluate(scroll_js)
            page.wait_for_timeout(1200)
            page.screenshot(path=f"{base}_{tag}.png")
        except Exception as e:
            print(f"   Screenshot ({tag}) nahi bani: {e}")

    top_js = """e => { let p = e.parentElement; while (p) { if (p.scrollHeight > p.clientHeight + 5 && getComputedStyle(p).overflowY !== 'visible') { p.scrollTop = 0; break; } p = p.parentElement; } }"""
    shot("1_top", top_js, page.locator("#formStudentName"))
    shot("2_uploads", "e => e.scrollIntoView({block: 'start'})", page.get_by_text("Photo & Aadhaar").first)
    shot("3_bottom", "e => e.scrollIntoView({block: 'end'})",
         page.locator("form:has(#formStudentName)").get_by_role("button", name=re.compile("Register")).first)
    if i == 1:                                         # sirf pehle student par: dhundhle parde ka pata
        info = describe_overlay(page)
        with open("proof/overlay_info.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(info))
        print("   Screen ke beech ke upar-upar elements (proof/overlay_info.txt mein bhi):")
        for line in info:
            print("     ", line)


def login_like(page):
    try:
        return page.locator("input[type=password]").count() > 0 or "login" in page.url.lower()
    except Exception:
        return False


def open_form(page):
    """Form na dikhe to portal ka "Register New Student" button dabakar form kholta hai."""
    try:
        page.wait_for_selector("#formStudentName", timeout=2000)
        return
    except Exception:
        pass
    btn = page.get_by_role("button", name=re.compile(OPEN_FORM_BUTTON, re.I)).first
    try:
        btn.click(timeout=15000)
    except Exception:
        page.get_by_text(OPEN_FORM_BUTTON).first.click(timeout=5000)
    page.wait_for_selector("#formStudentName", timeout=15000)


def ensure_form(page):
    """Tab mein form dikhe (button dabakar); nahi to batata hai kyun (login ya button) aur aapse khulwata hai."""
    try:
        open_form(page)
        return
    except Exception:
        pass
    if login_like(page):
        print("   Is tab mein LOGIN page aaya hai (session is tab mein nahi mili).")
    else:
        print("   Is tab mein form khud nahi khula.")
    input("   Is tab mein login/form kholiye, phir yahan Enter dabaiye... ")
    page.wait_for_selector("#formStudentName", timeout=30000)


def probe_new_tab(ctx):
    """Pehle student se pehle jaanch: kya naya tab seedha form kholta hai (login bina maange)?
    Jaanch theek rahi to wahi tab (form khula hua) wapas milta hai aur pehle student ke kaam aata hai."""
    pg = ctx.new_page()
    video = pg.video if RECORD_VIDEO else None
    ok, why = False, ""
    try:
        pg.goto(URL)
        open_form(pg)
        ok = True
    except Exception:
        why = "login page aaya (session naye tab mein nahi mili)" if login_like(pg) else "form nahi khula (button nahi mila ya form nahi aaya)"
    if ok:
        return ok, why, pg            # form khula hai: yahi tab pehle student ke liye use hoga (dobara button nahi dabana padega)
    pg.close()
    if video:
        try:
            video.delete()
        except Exception:
            pass
    return ok, why, None


def finish_page(page, i, s, status):
    """Tab band karta hai aur uski video ko videos/<no>_<naam>_<status>.webm naam se save karta hai."""
    video = page.video if RECORD_VIDEO else None
    page.close()                                  # video tab band hone par poori hoti hai
    if video:
        try:
            name = re.sub(r"[^a-z0-9]+", "_", s["student_name"].lower()).strip("_") or "student"
            dest = os.path.join(VIDEO_DIR, f"{i:03d}_{name}_{status}.webm")
            video.save_as(dest)
            video.delete()
            print(f"   Video: {dest}")
        except Exception as e:
            print("   Video save nahi hui:", e)


def main():
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        students = [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]

    os.makedirs("proof", exist_ok=True)

    with sync_playwright() as p:
        if RECORD_VIDEO:
            os.makedirs(VIDEO_DIR, exist_ok=True)
            size = SIZES[VIDEO_QUALITY]
            opts = dict(record_video_dir=VIDEO_DIR, record_video_size=size, viewport=size)
        else:
            opts = dict(viewport={"width": 1500, "height": 900})
        # Camera (aur baaki) permission popup apne aap "Block" ho jata hai: portal ka camera preview popup nahi dikhayega
        ctx = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False,
                                                   args=["--deny-permission-prompts"], **opts)
        print("Camera/permission popups auto-block par hain (--deny-permission-prompts): camera ka popup nahi aana chahiye.")
        login = ctx.pages[0] if ctx.pages else ctx.new_page()   # login tab; SINGLE_TAB mein isi mein kaam hota hai

        login.goto(LOGIN_URL)
        input("Login kar lijiye, phir yahan Enter dabaiye (register-student page aur form script khud kholegi)... ")

        first_page = None               # jaanch wala tab, pehle student ke liye
        if not SINGLE_TAB:
            ok, why, first_page = probe_new_tab(ctx)
            if ok:
                print("Jaanch OK: naya tab login maange bina khula aur 'Register New Student' se form khul gaya.")
            else:
                print(f"\nJAANCH FAIL: naye tab mein {why}.")
                print("Har student par naye tab mein aapko login/form khud kholna padega.")
                print("Behtar: script mein SINGLE_TAB = True karke dobara chalayein (saare students ek hi tab mein).")
                if input("Phir bhi naye tab se chalayein? (y/N): ").strip().lower() != "y":
                    ctx.close()
                    return
            try:
                login.goto("about:blank")   # bhaari portal page hata dete hain (RAM bachti hai); cookies profile mein save hain
            except Exception:
                pass

        for i, s in enumerate(students, 1):
            print(f"\n[{i}/{len(students)}] {s['student_name']}")
            for key in ("photo", "aadhaar_front", "aadhaar_back"):
                alt = os.path.join(IMAGE_DIR, s[key])
                if not os.path.isfile(s[key]) and os.path.isfile(alt):
                    s[key] = alt
            errs = validate(s)
            if errs:
                print("   SKIP - data mein galti:")
                for e in errs:
                    print("    -", e)
                continue

            reused = False
            if SINGLE_TAB:
                page = login               # ek hi tab; pehle student ke liye form pehle se khula maana jata hai
            elif first_page is not None:
                page = first_page          # jaanch wala tab: form pehle se khula hai
                first_page = None
                reused = True
                page.bring_to_front()
            else:
                page = ctx.new_page()      # har student ka alag tab = alag video
                page.bring_to_front()
            status = "error"
            try:
                if not (reused or (SINGLE_TAB and i == 1 and page.locator("#formStudentName").count() > 0)):
                    page.goto(URL)         # SINGLE_TAB mein pehle student ka form pehle se khula ho to dobara load nahi karte
                ensure_form(page)
                fill_student(page, s)
                capture_proof(page, i, s)

                if DRY_RUN:
                    status = "dryrun"
                    print("   DRY RUN: Register abhi nahi dabaya hai.")
                    ans = input("   Form check kijiye. Register dabane ke liye OK likhiye (ok bhi chalega), "
                                "ya sirf Enter dabakar bina register agla student... ")
                    if ans.strip().lower() != "ok":
                        continue
                    print("   OK mila: Register dabaya ja raha hai (DRY_RUN = True hone ke bawajood).")

                reg = page.locator("form:has(#formStudentName)").get_by_role("button", name=re.compile("Register"))
                try:
                    reg.click(timeout=10000)
                except Exception:
                    reg.evaluate("e => e.click()")     # agar koi parda mouse click rok raha ho
                page.wait_for_timeout(4000)
                page.screenshot(path=f"proof/{i:03d}_{s['student_name']}_result.png", full_page=True)
                status = "submitted"
                print("   Register dabaya - result screenshot proof/ folder mein hai")
            except Exception as e:
                print("   FAILED:", e)
                try:
                    page.screenshot(path=f"proof/{i:03d}_{s['student_name']}_error.png", full_page=True)
                except Exception:
                    pass
            finally:
                if not SINGLE_TAB:
                    finish_page(page, i, s, status)
                print(f"   Khule tabs ab: {len(ctx.pages)}")

        if first_page is not None:      # koi student process nahi hua to jaanch wala tab band karein
            try:
                fv = first_page.video if RECORD_VIDEO else None
                first_page.close()
                if fv:
                    fv.delete()
            except Exception:
                pass
        input("\nKhatam. Browser band karne ke liye Enter dabaiye... ")
        # Login tab ki video: normal mode mein hata dete hain (password/OTP dikh sakta hai).
        lv = login.video if RECORD_VIDEO else None
        lv_path = None
        try:
            lv_path = lv.path() if lv else None
        except Exception:
            pass
        try:
            login.close()
        except Exception:
            pass
        try:
            ctx.close()                 # video file band hone par poori hoti hai
        except Exception:
            pass
        if lv_path:
            if SINGLE_TAB and os.path.isfile(lv_path):
                dest = os.path.join(VIDEO_DIR, "all_students_INCLUDES_LOGIN.webm")
                os.replace(lv_path, dest)
                print(f"Video: {dest} (isme login screen bhi hai, share na karein)")
            else:
                try:
                    os.remove(lv_path)
                except Exception:
                    print("Login video haath se delete karein:", lv_path)


if __name__ == "__main__":
    main()
