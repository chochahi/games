# Bihar School Games – Student Registration Helper

A free toolkit that lets a teacher collect every student's registration details and documents **once**, in the right format, and then fill the official Bihar School Games registration form from that data.

> **Disclaimer:** Independent helper project. Not affiliated with or endorsed by the Bihar School Games portal or any government body. Use it only for students you are authorised to register, and follow the portal's terms.

## The problem

Per student the official form needs: name, gender, Aadhaar, date of birth, mother's and father's names, parent mobile, game, bank details (beneficiary, account number, IFSC), a passport photo and Aadhaar front/back images. **Each image must be up to 200 KB.** Collecting this over WhatsApp causes oversized images, missing files and "whose file is this?" confusion.

## What this project does

1. Students open **one link** and fill a form (on a phone is fine).
2. Photo and Aadhaar images are **compressed in the browser to about 185–190 KB** automatically.
3. The submission is packaged under a **predictable name** (`name_classN_last4`), either as a zip the student sends, or directly into your Google Sheet/Drive.
4. The teacher sees **who has submitted and who is pending**.
5. A Playwright script logs in once and then fills the official form for each student from the collected data (one browser tab per student, an optional video of each), with a dry-run mode to check first.

## Two modes (same `index.html`)

| | **Zip mode** | **Google Sheet mode** |
|---|---|---|
| Student link | Plain GitHub Pages link | Link generated in the teacher panel (carries your Web app URL and access code in the `#` part) |
| Student action | Submit → zip is saved → **WhatsApp** button opens your chat (student attaches the zip); a **Share** button appears where the browser allows file sharing | Submit → data and images go straight to your Google account |
| Where data lands | In the zips the students send you; you load them in the teacher panel | Google Sheet (`Students`) + Drive folder |
| Pending tracker | Teacher panel (class list, saved in your browser) | `Roster` tab in the Sheet (live) |
| Setup | GitHub Pages only | + Google Sheet, Apps Script, deployment |
| Backend / public endpoint | None | Google Apps Script Web app (access-code protected) |
| Main privacy exposure | Zips sit in students' phones and WhatsApp | Your Google account; endpoint reachable by anyone with the link |
| Best for | Simple setups, minimal moving parts | Many students, hands-off collection |

If the Google server is unreachable, Google mode automatically falls back to downloading a zip, so both flows can coexist.

## Naming convention

Everything a student submits is named **`<name>_class<N>_<last 4 digits of Aadhaar>`**:

| Item | Example |
|---|---|
| Zip file | `ravi_kumar_class8_9012.zip` |
| Inside the zip | `data.json`, `photo.jpg`, `aadhaar_front.jpg`, `aadhaar_back.jpg` |
| Drive images (Google mode) | `ravi_kumar_class8_9012_photo.jpg`, `..._aadhaar_front.jpg`, `..._aadhaar_back.jpg` |
| Batch export | `photos/ravi_kumar_class8_9012.jpg`, `aadhaar/ravi_kumar_class8_9012_front.jpg` / `_back.jpg` |

Names are lower-cased; any run of characters other than `a–z` and `0–9` becomes `_`. A name written only in Devanagari becomes `student`, so the file is still identified by class and last 4 digits (and by `data.json`). The **full Aadhaar** is the real unique key used for de-duplication.

## Game eligibility (age category and gender)

The game dropdown shows **only eligible games**. The form works out the age category from the date of birth (age on **1 March 2027**, the date the portal uses) and the chosen gender:

| Game | Categories | Who |
|---|---|---|
| Football | U-14, U-16 | Boys only |
| Kabaddi | U-14, U-16 | Boys & Girls |
| Volleyball | U-16 | Boys only |
| Cycling (3km) | U-14 | Boys & Girls |
| Cycling (5km) | U-16 | Boys & Girls |
| Long Jump (Athletics) | U-14, U-16 | Boys & Girls |
| 60m Sprint (Athletics) | U-14 | Boys & Girls |
| 100m Sprint (Athletics) | U-16 | Boys & Girls |
| 600m Long Run (Athletics) | U-14 | Boys & Girls |
| 800m Long Run (Athletics) | U-16 | Boys & Girls |

Assumed age rule (verify against the portal's own Category field): **U-14 = age 13 or less, U-16 = age 14 or 15** on 1 March 2027. A student older than 15 (for example 18) has no eligible game and cannot be submitted.

## Features

- Mobile-friendly form with validation: Aadhaar 12 digits, mobile 10 digits, IFSC pattern, account number digits, beneficiary name must equal student's, mother's or father's name, all three images required
- Single-select dropdowns for **Class (1–12)** and **Game**; the game list is filtered by gender and age category (see above) and shows the computed age and category under the dropdown
- The server (Google mode) re-checks eligibility and stores the `category` in the Sheet
- Browser-side JPEG compression to just under 200 KB (target 185–190 KB), EXIF rotation respected
- Re-submitting the same Aadhaar **replaces** the earlier entry instead of duplicating
- Teacher panel: add many zips at once, data survives refresh, class list with optional class (`Ravi Kumar, 8`), received/pending counts, spelling-mismatch hints, copy-pending-list for reminders, batch export
- Automation script (Playwright): dry-run mode (type `OK` at the prompt to really register just that student); checks every row first (Aadhaar, mobile, IFSC, beneficiary, image size, Excel-damaged numbers); logs in once and reuses the session; opens the form with the portal's **Register New Student** button (the self-check tab is reused for the first student, so the form opens once); hides the portal's dimming accessibility overlay; blocks the camera popup; waits for Age/Category to fill; picks the game from the portal's own dropdown; uploads each image by its box label; one tab per student that is closed afterwards (low memory); proof screenshots and optional **per-student video** (720p/1080p)

## Repository layout

```
.
├── index.html                    Student form (GitHub Pages)
├── teacher.html                  Teacher panel (zip tracker/merge + optional Google link generator)
├── apps-script/
│   └── Code.gs                   Google Apps Script backend (Google mode only)
├── automation/
│   ├── register_students.py      Playwright script that fills the official form
│   ├── students.sample.csv       Example CSV (copy to students.csv)
│   └── requirements.txt
├── docs/
│   ├── architecture.md           Design, data model, security, internals
│   └── setup_guide.md            Step-by-step setup and operations for both modes
├── .gitignore                    Keeps student data out of Git
└── README.md
```

Created while the tools run (all git-ignored): `proof/` (screenshots), `videos/` (recordings), `pw_profile/` (saved portal login), `images/` (Drive images in Google mode).

## Quick start

**Zip mode**
1. Push the repo to GitHub, enable Pages (branch `main`, root).
2. Put your WhatsApp number in `index.html` (`TEACHER_WHATSAPP`, e.g. `919876543210`) and send **every student the same link** `https://<user>.github.io/<repo>/`. After Submit, a **WhatsApp** button opens your chat with a prefilled message; the student attaches the saved zip.
3. Load their zips into `…/teacher.html`, paste your class list, watch the pending list shrink.
4. Export the batch zip and run the automation script.

**Google Sheet mode**
1. Do step 1 above. Create a Google Sheet, paste `apps-script/Code.gs`, run `setup`, deploy as a Web app.
2. In `teacher.html` open *Google Sheet mode*, paste the Web app URL + access code, generate the student link.
3. Share that link. Watch the Sheet fill up.
4. Download the Sheet as CSV and the Drive folder as `images/`, run the automation script.

Details for every step: **[docs/setup_guide.md](docs/setup_guide.md)**. How it all works: **[docs/architecture.md](docs/architecture.md)**.

## Running the automation

```bash
cd automation
pip install -r requirements.txt
playwright install chromium
python register_students.py          # DRY_RUN = True by default: fills the form, never submits
```

1. Put `students.csv` (never open it in Excel) and the images (`photos/` + `aadhaar/` from the batch zip, or `images/` from Drive) next to the script.
2. A browser opens on the portal's login page. Log in, then press Enter in the terminal.
3. The script checks that a new tab stays logged in and can open the form, fills the first student in that tab and each later student in a fresh tab, and pauses after each one in dry-run mode. At the prompt press **Enter** to skip registering, or type **OK** to click **Register** for that student.
4. When the dry run looks right, set `DRY_RUN = False` and run again. After each student it clicks **Register** and saves a screenshot to `proof/`. (To test the real submission on one student first, keep `DRY_RUN = True` and type `OK` for that student only.)

Settings at the top of `register_students.py`:

| Setting | Default | Meaning |
|---|---|---|
| `DRY_RUN` | `True` | Fill but do not click Register (at the prompt, typing `OK` clicks it for that student) |
| `OPEN_FORM_BUTTON` | `"Register New Student"` | Text of the portal's button that opens the form |
| `SINGLE_TAB` | `False` | `True` = process every student in the one tab you logged into (fallback if new tabs do not keep the login) |
| `RECORD_VIDEO` | `True` | One video per student in `videos/`; set `False` on a slow PC |
| `VIDEO_QUALITY` | `"720p"` | `"720p"` or `"1080p"` (1080p only on a big monitor) |
| `LOGIN_URL`, `URL` | portal login / register-student pages | Change only if the portal moves |

Videos and screenshots show Aadhaar numbers, bank details and children's photos: keep them private and delete them after verification. See the setup guide (Part 4) for details and troubleshooting.

## Privacy and responsible use

You are handling **children's personal data, including Aadhaar and bank details**.

- The repo holds **code only**. Never commit real data (`.gitignore` excludes `students.csv`, `images/`, `photos/`, `aadhaar/`, `proof/`, `videos/`, `pw_profile/`, `*.zip`).
- Zip mode: ask students to delete the zip from their phone/WhatsApp after sending. Clear the teacher panel (**Sab hatayein**) when done.
- Google mode: keep the Sheet and Drive folder private; use 2-step verification on that Google account.
- Delete everything when the registration period ends.
- The form currently has **no consent checkbox or privacy notice**. Check with your school/education department what consent is required for minors' data.

## Known limitations

- The automation script was built and tested against a **mock portal** (login by cookie/localStorage/sessionStorage, button-opened form, tab and video handling), then dry-run on the **live portal with one student**: all fields, auto Age/Category, game selection and the three uploads were confirmed in screenshots and video. The real **Register** click and the portal's response have **not** been confirmed yet, so keep checking `proof/` after the first real submissions.
- OTP/CAPTCHA on the portal needs a person.
- The age rule (U-14 = 13 or less, U-16 = 14–15 on 1 March 2027) and the labels of the games are partly assumptions. Confirmed live so far: the label **Volleyball** and one U-16 Boys case (15 years 11 months 20 days). The labels of the three newer games (100m Sprint, 800m Long Run, Cycling (5km)) and girls'/U-14 cases are still unverified; check them against the portal's Category field and dropdown.
- A web page cannot open WhatsApp with a file already attached: the WhatsApp button opens the chat, and the student attaches the zip with the paperclip.
- If the portal is down, collection still works; only the automation step waits (see the setup guide). The script has no resume feature: remove already-registered students from the CSV before rerunning.
- The script does not pause for OTP/CAPTCHA during a real run, and it will not click anything it does not know (only the **Register New Student** and **Register** buttons).
- Never open `students.csv` in Excel: it corrupts long numbers (Aadhaar, account number) and dates.
- Google mode's access code is a spam filter, not strong authentication.
- The Sheet's `Roster` tab matches by **name only**; the teacher panel's roster can also match by class.
- Google quotas apply to Apps Script and Drive; fine for a school, but check Google's current limits for very large batches.

## What has and has not been tested

| Tested | Not tested |
|---|---|
| Age-category rule against 3,288 dates of birth (form and `Code.gs` logic) | The real **Register** click and the portal's response on the live portal |
| Live-portal **dry run**, one student (U-16 boy, Volleyball): form fill, auto Age/Category, game select and three uploads, seen in screenshots and video | Other game labels; girls' and U-14 cases on the live portal |
| Script on a mock portal: new-tab login for cookie/localStorage, session fallback, button-to-open form, per-student tabs (flat memory over 30 students), 720p/1080p video | Apps Script on a real Google account |
| Syntax of `index.html`, `teacher.html`, `Code.gs`, `register_students.py`; matching/fuzzy hints in the teacher panel | The student form and teacher panel in real phone browsers (including the WhatsApp and Share buttons) |

Do a full trial with one test student in each mode before sharing the link with a class.

## Recent changes to the automation script

- **Upload scrolling:** the portal's form is a modal with its own scrollbar; the script now scrolls that container to each upload box and pauses so the video shows the previews.
- **Overlay hidden:** the portal's accessibility widget dimmed the screen and blocked mouse clicks (`#accessibility-overlay`); the script hides it.
- **Camera popup blocked:** Chromium starts with `--deny-permission-prompts`.
- **Type `OK` in dry run:** registers just that student without turning `DRY_RUN` off.
- **Form opens once:** the self-check tab is reused for the first student instead of being closed and reopened.
- **Login video cleanup:** the browser is closed first and the login video file is then deleted by path (no more `Video.delete` error).

## Tech stack

Plain HTML/CSS/JavaScript (no build step) · JSZip from cdnjs · browser IndexedDB/localStorage (zip mode tracker) · Google Apps Script, Sheets, Drive (Google mode) · Python 3 + Playwright (automation)
