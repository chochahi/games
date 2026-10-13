# Setup Guide (Zip mode and Google Sheet mode)

## 0. Choose your mode

| Question | Zip mode | Google Sheet mode |
|---|---|---|
| Need a Google account setup? | No | Yes |
| How do submissions reach you? | Students send zips (Share/WhatsApp) | Automatically into your Sheet + Drive |
| Pending tracker | Teacher panel | Roster tab |
| Effort | ~10 minutes | ~30–40 minutes |

Both need **Part 1** (GitHub Pages) and, to fill the official form, **Part 4** (automation). You can run both modes with the same site; they differ only in the link you give students.

**Requirements:** GitHub account; Google account (Google mode); Chrome; Python 3.9+ (automation).

---

## Part 1 – Host on GitHub Pages (both modes)

1. Create a **new public repository**, e.g. `bihar-school-games`. (Free GitHub Pages needs a public repo; this is fine because the repo contains code only, never student data.)
2. Upload the files keeping the layout from the README. `index.html` and `teacher.html` must be in the **repo root**.
   - Web UI: **Add file → Upload files → Commit changes**, or
   - git:
     ```bash
     git init && git add . && git commit -m "Initial commit"
     git branch -M main
     git remote add origin https://github.com/<user>/bihar-school-games.git
     git push -u origin main
     ```
3. **Settings → Pages** (labels may change over time): Source *Deploy from a branch*, branch `main`, folder `/ (root)`, **Save**.
4. After 1–2 minutes your URLs are:
   - Student form: `https://<user>.github.io/bihar-school-games/`
   - Teacher panel: `https://<user>.github.io/bihar-school-games/teacher.html` (bookmark it; do not share it with students)

Updating later: commit the change; Pages redeploys within a couple of minutes; hard-refresh (Ctrl+Shift+R) to see it.

---

## Part 2 – Zip mode

### 2.0 Set your WhatsApp number once (recommended)
In `index.html`, near the top of the script, set `const TEACHER_WHATSAPP='91XXXXXXXXXX';` (country code + number, digits only, no `+` or spaces), commit, and wait for Pages to redeploy. Every student then uses the **same plain GitHub Pages link**, and the **WhatsApp** button after Submit opens a chat with you with a prefilled message. You never send individual links.

Notes:
- The repo is public, so this number becomes publicly visible in the code. If you prefer not to publish it, leave the constant empty and use `teacher.html` → *Student link (Zip mode)* to create a link ending in `#w=<number>` (open `teacher.html` from your GitHub Pages URL, not from a preview or local file, or the generator will refuse).
- A `#w=` in the link overrides `TEACHER_WHATSAPP`, so different classes can use different numbers.
- The browser cannot open WhatsApp automatically without a tap, and it cannot attach the file. The student taps the button, then attaches the saved zip with 📎.

### 2.1 What students do
1. Open the student link (the plain `https://<user>.github.io/bihar-school-games/` or the one with `#w=...`).
2. Fill every field: name, **class**, gender, Aadhaar, **date of birth**, parents' names, mobile, optional e-mail, bank details. The **game** list appears after gender and date of birth are chosen and contains only the games that student is eligible for (the page shows the age on 1 March 2027 and the category). A student over 15 has no eligible game and cannot submit.
3. Choose three images (photo, Aadhaar front, Aadhaar back). Each shows its compressed size, about 185–190 KB if the original was large.
4. Tap **Submit**. A file like `ravi_kumar_class8_9012.zip` is created.
5. After Submit the zip is saved to the phone. Tap **WhatsApp ... kholein** (it opens your chat with the prefilled message), then tap 📎 → **Document** and pick the zip from Downloads. If a **Share karein** button is also shown, it can attach the file directly. WhatsApp cannot be opened with the file already attached by a web page.
6. Delete the zip from the phone afterwards.

### 2.2 What the teacher does
1. Open `teacher.html`.
2. Paste the **class list**, one student per line: `Ravi Kumar, 8` (name and class) or just `Ravi Kumar`. It is remembered in this browser. With a class on the line, both name and class must match; spell names exactly as students will write them.
3. Under *Bachchon ki zip files*, select the received zips. You can select many at once and come back later to add more; everything is kept (IndexedDB) even after a refresh.
4. Read the status: `done/total mil gaye`, **Baaki** and **Mil gaye** lists.
   - A pending name followed by *(shayad "X" ne bheja – spelling/class check karein)* means a similar name or the same name with a different class was received; fix the list or ask the student.
   - ⚠ on a received student means they are not on your list.
   - **✕** removes a wrongly added entry.
5. **Baaki list copy karein** copies the pending names for a WhatsApp reminder.
6. When everyone is in, click **Download batch zip**. Extract it into the `automation/` folder (Part 4). It contains `students.csv`, `photos/` and `aadhaar/`.
7. When all work is finished, click **Sab hatayein** and delete the zips from your phone/computer.

The tracker only knows about zips you have loaded; a zip a student sent but you have not yet added shows as pending.

---

## Part 3 – Google Sheet mode

### 3.1 Sheet and script
1. Open <https://sheets.new>, name it e.g. `Bihar School Games Registrations`. **Use a new, empty Sheet** (if you ran an older version, do not reuse its `Students` tab: the column layout now includes `class`).
2. **Extensions → Apps Script**. Delete the sample code and paste all of `apps-script/Code.gs`.
3. Change `ACCESS_CODE` to your own secret word. Do **not** commit your real code to GitHub. **Save**.

### 3.2 Run `setup` once
1. Choose function **`setup`** and click **Run**.
2. Authorise: **Review permissions → your account → Advanced → Go to (project) (unsafe) → Allow**. This warning appears for any personal script Google has not reviewed; it is your own script, and it will have access to your Drive, which is why a dedicated Google account is wise.
3. Result: tabs **Students** (headers) and **Roster**, and a Drive folder **Bihar School Games - Images**.

### 3.3 Deploy
1. **Deploy → New deployment →** gear → **Web app**.
2. *Execute as:* **Me**; *Who has access:* **Anyone**. **Deploy**, copy the URL ending in `/exec`.
3. After any later change to `Code.gs`: **Deploy → Manage deployments → ✏️ → Version: New version → Deploy**, otherwise the old code keeps running.

### 3.4 Generate the student link
1. Open `teacher.html`, expand **Google Sheet mode (optional)**.
2. Paste the Web app URL and the access code, click **Link banao**.
3. Copy the long link (`…/#u=…&c=…`). Give **only this** link to students. Use the plain link only if you want zip mode.

### 3.5 Test
1. Open the generated link and submit a test student with three sample images.
2. You should see "registration teacher tak pahunch gaya".
3. Check **Students** (new row, including `class` and `category`) and the Drive folder (three files named `<base>_photo.jpg` etc., each about 185–190 KB for large originals).
4. Delete the test row and the test images.

### 3.6 Track who is pending
Paste the class list into **Roster** column A. Column B shows **✓ Mil gaya** or **Baaki**. This tab matches **names only** (not class), so spelling must match exactly (case-insensitive). If you also want class-aware tracking, export the Sheet and use the teacher panel's batch workflow, or tell the maintainer to extend the Roster formula.

Re-submitting the same Aadhaar replaces that student's row and images.

### 3.7 If a student cannot reach the server
The page downloads a zip instead (message shown). Treat it like zip mode: load it in `teacher.html`, or ask the student to retry later.

---

## Part 4 – Fill the official form (both modes)

### 4.1 Install (once)
```bash
cd automation
pip install -r requirements.txt
playwright install chromium
```

### 4.2 Prepare the data
- **Zip mode:** extract the batch zip into `automation/` → you now have `students.csv`, `photos/`, `aadhaar/`.
- **Google mode:** in the Sheet open **Students → File → Download → CSV**, save as `automation/students.csv`. In Drive, download the folder **Bihar School Games - Images**, extract to `automation/images/`.

The CSV has the columns `student_name, gender, aadhaar, dob, mother_name, father_name, mobile, email, game, beneficiary_name, account_number, ifsc, class, category, photo, aadhaar_front, aadhaar_back` (Google mode adds `submitted_at` and link columns). Extra columns such as `class`, `category` or `submitted_at` are not used, except that `category` is compared with the portal's category as a check. **Never open the CSV in Excel**: it turns Aadhaar/account numbers into `6.33274E+11` and rewrites dates, and the script will reject such rows. View it in Notepad, or import with every column set to **Text**. If it is already damaged, export a fresh CSV (zip mode: download the batch zip again from the teacher panel).

### 4.3 Dry run (default)
`DRY_RUN = True`. Before running, open the portal's registration form **fresh** (refresh the page), because a half-filled form from an earlier run keeps old values and error messages. Run `python register_students.py`. A Chromium window opens on the portal's login page (`https://www.biharsportsmashaal.in/school/login`); log in and press Enter in the terminal. The script then opens the registration page (`.../pages/register-student`) itself and clicks the blue **Register New Student** button to open the form. The script fills the first student and **stops** so you can verify. At the prompt press **Enter** to move to the next student without registering, or type **OK** (or `ok`) and press Enter to click **Register** for that student even though `DRY_RUN` is `True`; this lets you test the real submission one student at a time. Chromium is started so that the portal's camera popup is blocked automatically (a line in the terminal confirms it). Order: name, gender, Aadhaar, date of birth (waits until Age fills), parents, mobile, e-mail, game (opened and chosen with the keyboard from the portal's own list), bank details, then the three uploads. Check: **date of birth**, **age/category auto-filled**, **game**, **three uploads in the right boxes**.

| Problem | Fix |
|---|---|
| "DOB '…' ke baad Age nahi bhari. Portal ka message: …" | The portal did not calculate age, usually with its own message such as "You are not allowed to register due to age restrictions". Type the same DOB by hand in the portal: if Age/Category stay empty, the portal does not accept that age, so that student cannot be registered in these categories. If typing by hand works, send the maintainer the video |
| Form goes grey/dim and the game cannot be clicked | Seen in a recorded run: typing the DOB slowly made the portal flag partial dates (for example `0` read as 01/01/2000) with an age-restriction error. The script now fills the whole DOB at once. If the dim still appears, send the video |
| Screen looks grey/dim, clicks seem ignored | The portal's accessibility widget puts a 40% black layer (`#accessibility-overlay`) over the page. The script now hides it. If the screen is still dim, send `proof/overlay_info.txt` (its first line shows what covers the page) and the video |
| Chrome asks "wants to use available cameras" | The script blocks this popup automatically. If it still appears, click **Never allow** once; the choice is saved in `pw_profile/` |
| Red "Invalid credentials" banner on the student list in a new tab | Seen once in a recorded run and not reproduced; the form still opened and filled. If a real Register fails with this message, set `SINGLE_TAB = True` and run again |
| Camera boxes are black | Normal: the portal's camera preview needs permission. The script never uses the camera (uploads only) |
| "Game '…' options mein nahi mila. Portal ke options: [...]" | The label differs from the portal's. Compare with the printed list and fix `GAMES` in `index.html` (and `Code.gs`) or the CSV value |
| "Game dropdown mein koi option nahi aaya" | No options for that gender/category; check Age and Category filled correctly |
| Warning "hamari category … portal ne …" | The portal and the form disagree on the category (cut-off rule). Check the rule in `CATS` |
| "scientific notation (E+)" | CSV was opened/saved in Excel. Export a fresh CSV |
| "upload ke baad box nahi badla" | The portal did not accept that image; check its size (must be under 200 KB) and format |
| Row skipped with data error | Fix that row (rules are printed in the message) |
| Form not found for later students | Open the form manually or adapt the script to click the portal's register button |
| OTP / CAPTCHA | Needs a person; the script has no built-in pause for it during a real run |

### 4.4 Real run
Set `DRY_RUN = False`, run again. After each student the script clicks **Register** and saves screenshots to `proof/`. Review `proof/` for errors. To try the real submission on a single student first, keep `DRY_RUN = True` and type `OK` at the prompt for that student only. Registration cannot be undone by the script and there is no resume, so do not type `OK` twice for the same student.

---

### 4.5 Video recording (verify and debug)

The script records a **video of each student's browser tab** (settings at the top of `register_students.py`):

```python
RECORD_VIDEO = True      # False to switch off
VIDEO_QUALITY = "720p"   # or "1080p"
VIDEO_DIR = "videos"
```

- Each student gets `videos/<no>_<name>_<status>.webm` where status is `dryrun`, `submitted` or `error`, so a failed student's video can be opened directly. Play `.webm` in Chrome or VLC.
- `720p` (1280x720) is the default and is fine on most laptops. Use `1080p` only on a monitor larger than 1920x1080 (the browser window is sized to the recording).
- Before each upload the script scrolls the portal's form (a modal with its own scrollbar) to the upload box and pauses briefly, so the video shows the three previews appear. A dimming accessibility overlay used to hide this; the script now removes it.
- It records the **page content only**: no address bar, mouse pointer or other windows. For a full-screen recording with the pointer, use a screen recorder (for example Windows Game Bar, `Win+Alt+R`, or OBS) alongside the script.
- Videos are written when each tab closes, so a crashed student still gets a video; a hard kill of the script may leave an unfinished file.
- The login tab is recorded too but its video is deleted at the end of a normal run. If the script is killed, delete the leftover random-named `.webm` in `videos/` by hand (it can show login details). At the end the script closes the browser first and then deletes the file by its path.
- **Videos show Aadhaar numbers, bank details and children's photos.** Keep `videos/` private, never commit it (it is in `.gitignore`), and delete it when the registration is verified.
- **Only one student tab is open at a time.** The tab is closed after every student, whether the registration succeeded, was only a dry run, or failed, and only then the next tab opens. Right after login the heavy portal page is replaced with a blank tab (kept only so the browser stays open), and the console prints `Khule tabs ab: 1` after each student. Measured on a dummy page over 30 students: 1 tab throughout and memory flat (about 356 MB to 358 MB); with tabs left open it grew by roughly 115 MB per student. The real portal page is heavier, so absolute numbers will be higher, but memory stays flat.
- **No second login needed (normally).** Playwright keeps the login in the profile (`pw_profile/`) and a new tab in the same browser shares cookies and `localStorage`, so turning the login tab blank does not log you out. Tested on a mock portal in real Chromium: with a cookie login or a `localStorage` login the new tab opened the page already logged in; with a `sessionStorage` login (which is per tab) it did not. I could not test the real portal.
- **Self-check before the first student.** After you press Enter at login, the script opens a temporary tab, loads the form URL and checks that the form appears. It prints `Jaanch OK` or `JAANCH FAIL` with the reason: *login page aaya* (session not shared with new tabs) or *form nahi khula* (the button was not found or the form did not appear). On failure it asks whether to continue; if you answer no, set `SINGLE_TAB = True` and run again. When it passes, that same tab (form already open) is used for the first student, so the form opens once; later students each get a fresh tab.
- **`SINGLE_TAB = True` (fallback):** all students are processed in the one tab you logged into (open the form there before pressing Enter; the script reloads the URL for the next students). Memory stays low, but there is **one** video for the whole run, `videos/all_students_INCLUDES_LOGIN.webm`, which also shows the login screen, so do not share it.
- **Opening the form:** `/pages/register-student` first shows a list of registered students with a blue **Register New Student** button (seen in a screenshot of the portal). The script clicks that button (`OPEN_FORM_BUTTON` at the top of `register_students.py`) whenever the form is not already open. If the button is not found it asks you to open the form by hand and press Enter. In the same screenshot a new tab opened straight after login did not ask to log in again.
- **Low-end PC:** recording itself costs CPU and memory. If the computer is slow, set `RECORD_VIDEO = False` (screenshots in `proof/` are still saved), keep `VIDEO_QUALITY = "720p"`, and close other programs and browsers.
- If the form does not appear in a new tab within 10 seconds, the script asks you (once per student) to open the form in that tab and press Enter.

---

## Part 5 – Message to send students (copy/paste)

> Bihar School Games registration ke liye yeh link kholein: **<link>**.
> Form poora bharein. Game ki list gender aur date of birth chunne ke baad dikhegi (sirf wahi game jinke aap eligible hain). Teeno photos daalein (passport photo, Aadhaar front, Aadhaar back). **Submit** dabayein.
> *(Zip mode)* Jo file banegi (jaise `naam_class8_9012.zip`) use "Share" se mujhe bhej dein, phir apne phone se delete kar dein.
> *(Google mode)* "Registration pahunch gaya" likha aaye to kaam poora. Kuch nahi bhejna.
> Link kisi aur ko forward na karein.

---

## Part 6 – Operations and cleanup

- **Change games, eligibility or classes:** edit `GAMES` / `CATS` / `AGE_REF` / `CLASSES` in `index.html` (and keep `GAMES` and `category_()` in `Code.gs` the same), commit, hard-refresh. Game labels must match the portal.
- **Change image size limit:** `LIMIT` in `index.html` (and the per-image cap in `Code.gs`).
- **Link leaked (Google mode):** change `ACCESS_CODE`, deploy a **New version**, regenerate and re-share the link.
- **Security checklist**
  - [ ] Repo is code only; real data files are in `.gitignore`.
  - [ ] Real `ACCESS_CODE` exists only in your Apps Script and generated link.
  - [ ] Sheet and Drive folder are shared with nobody else; Google account has 2-step verification.
  - [ ] `teacher.html` URL is not shared with students.
  - [ ] After registration: delete Sheet rows, Drive folder, local `students.csv`, `images/`, `photos/`, `aadhaar/`, `proof/`, `videos/`, `pw_profile/`, and clear the teacher panel.
  - [ ] You have checked what consent/privacy notice your school requires for minors' data.

## If the official portal is down

Only Part 4 needs the portal. The student form, the Sheet/Drive, the zips and the teacher panel all keep working, so keep collecting.

- Nothing is lost: `students.csv`, the images (or the batch zip) and the teacher-panel data stay where they are.
- If the portal fails during a run, each affected student shows `FAILED` with an error screenshot in `proof/`. Rerun later.
- The script has **no resume feature**: it does not know who was already registered. Before rerunning, remove the students that were already submitted from the CSV (keep a copy of the full CSV), otherwise they may be submitted twice; how the portal treats duplicates is not known.
- Do a **dry run again** once the portal is back; the portal may have changed.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Student sees "Server tak nahi pahunch paya" and gets a zip (Google mode) | Web app not deployed as *Anyone*, wrong URL, or no internet. Recheck 3.3 and regenerate the link |
| "Access code galat hai" | Code in the link differs from `ACCESS_CODE`; regenerate the link or deploy a new version |
| Code change has no effect | Deploy a **New version** (3.3) |
| New page version not showing | Pages still building or cached; wait and hard-refresh |
| No Share button | Browsers only allow some file types to be shared (a `.zip` often is not). Use the WhatsApp button and attach the saved zip from Downloads |
| Teacher panel shows student as pending though received | Name/class mismatch with your list; read the hint, fix spelling or class |
| Zip "Padh nahi payi" | Not a zip from this app, or corrupt; ask the student to resubmit |
| Link generator says URL invalid | URL must start with `https://script.google.com/macros/s/` and end with `/exec` |
| Hindi-only name gives `student_class8_…` | Expected: the file name keeps only a–z/0–9; class and last 4 digits still identify it |
| Image over 200 KB | Should not happen; confirm students used the current `index.html` |
| Sheet column order looks wrong | Reused an old Sheet; create a new one and run `setup` again |
| "Koi game eligible nahi" on the form | The student's age on 1 March 2027 is outside U-14/U-16 (13 or less / 14–15). Check the DOB; if it is correct that student cannot be registered in these categories |
| Game list empty or "Pehle gender aur date of birth chunein" | Choose gender and date of birth first |
| Server says "Game is gender/age category ke liye eligible nahi hai" | `GAMES` in `Code.gs` differs from `index.html`, or the page is an old cached version. Keep both identical and deploy a **New version** |
| WhatsApp button opens a contact chooser | `TEACHER_WHATSAPP` is empty and the link has no `#w=` |

## FAQ

**Can I use both modes at once?** Yes. Give some students the plain link and others the generated link; both feed the same automation.
**What if two students share a name?** Use `Name, Class` in the teacher panel list. Files stay distinct by class and Aadhaar last 4 digits.
**Why last 4 Aadhaar digits, not all?** Keeps the file name useful without exposing the full number in chats or folders. Full Aadhaar is inside the zip/Sheet.
**Where is the data stored in zip mode?** In the zips themselves and, after loading, in your browser's IndexedDB on the teacher panel's origin.
