// Bihar School Games - registration collector.
// Google Sheet ke Extensions > Apps Script mein poora code paste karein.

const ACCESS_CODE = 'CHANGE_ME_BEFORE_USE';
const COLS = ['student_name','gender','aadhaar','dob','mother_name','father_name','mobile','email','game','beneficiary_name','account_number','ifsc','class','category'];
const IMGS = ['photo','aadhaar_front','aadhaar_back'];
const HEADERS = COLS.concat(IMGS, ['submitted_at','photo_link','aadhaar_front_link','aadhaar_back_link']);

// Eligibility: game -> [categories, genders]. index.html ke GAMES se match rehna chahiye.
const GAMES = {
  'Football': [['U-14','U-16'], ['Boy']],
  'Kabaddi': [['U-14','U-16'], ['Boy','Girl']],
  'Volleyball': [['U-16'], ['Boy']],
  'Cycling (3km)': [['U-14'], ['Boy','Girl']],
  'Cycling (5km)': [['U-16'], ['Boy','Girl']],
  'Long Jump (Athletics)': [['U-14','U-16'], ['Boy','Girl']],
  '60m Sprint (Athletics)': [['U-14'], ['Boy','Girl']],
  '100m Sprint (Athletics)': [['U-16'], ['Boy','Girl']],
  '600m Long Run (Athletics)': [['U-14'], ['Boy','Girl']],
  '800m Long Run (Athletics)': [['U-16'], ['Boy','Girl']]
};
// Age 1 March 2027 ko (dob = dd/mm/yyyy). Under-N = umar N se kam (anumaan: portal se verify karein).
function category_(dob) {
  const p = String(dob).split('/').map(Number);
  if (p.length !== 3 || !p[2]) return '';
  let a = 2027 - p[2];
  if (3 < p[1] || (3 === p[1] && 1 < p[0])) a--;
  return a < 0 ? '' : a <= 13 ? 'U-14' : a <= 15 ? 'U-16' : '';
}

// Ek baar chalayein (Run). Sheets aur Drive folder bana deta hai.
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName('Students') || ss.getSheets()[0].setName('Students');
  sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
  sh.setFrozenRows(1);
  const ro = ss.getSheetByName('Roster') || ss.insertSheet('Roster');
  ro.getRange('A1:B1').setValues([['Class ki list (naam yahan paste karein)', 'Status']]).setFontWeight('bold');
  const f = [];
  for (let r = 2; r <= 500; r++) f.push(['=IF(A' + r + '="","",IF(COUNTIF(Students!A:A,A' + r + ')>0,"✓ Mil gaya","Baaki"))']);
  ro.getRange(2, 2, 499, 1).setFormulas(f);
  const p = PropertiesService.getScriptProperties();
  if (!p.getProperty('FOLDER_ID')) p.setProperty('FOLDER_ID', DriveApp.createFolder('Bihar School Games - Images').getId());
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const d = JSON.parse(e.postData.contents);
    if (d.code !== ACCESS_CODE) return out_(false, 'Access code galat hai');
    if (!d.student_name || !d.class || !/^\d{12}$/.test(d.aadhaar || '') || !/^\d{10}$/.test(d.mobile || '')) return out_(false, 'Data adhoora ya galat hai');
    for (const k of IMGS) {
      if (!d.images || !d.images[k] || d.images[k].length > 330000) return out_(false, k + ' image missing ya badi hai');
    }
    d.category = category_(d.dob || '');
    const gm = GAMES[d.game];
    if (!d.category || !gm || gm[0].indexOf(d.category) < 0 || gm[1].indexOf(d.gender) < 0) return out_(false, 'Game is gender/age category ke liye eligible nahi hai');
    const folder = DriveApp.getFolderById(PropertiesService.getScriptProperties().getProperty('FOLDER_ID'));
    const id = (d.student_name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'student') + '_class' + d.class + '_' + d.aadhaar.slice(-4);
    const names = {}, links = {};
    IMGS.forEach(k => {
      names[k] = id + '_' + k + '.jpg';
      const old = folder.getFilesByName(names[k]);          // dobara submit hone par purani file hata dete hain
      while (old.hasNext()) old.next().setTrashed(true);
      links[k] = folder.createFile(Utilities.newBlob(Utilities.base64Decode(d.images[k]), 'image/jpeg', names[k])).getUrl();
    });
    const row = COLS.map(c => String(d[c] || ''))
      .concat(IMGS.map(k => names[k]), [new Date().toLocaleString('en-IN', {timeZone: 'Asia/Kolkata'})], IMGS.map(k => links[k]));
    const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Students');
    const last = sh.getLastRow();
    let r = last + 1;
    if (last > 1) {                                          // same Aadhaar dobara aaye to wahi row update hogi
      const i = sh.getRange(2, 3, last - 1, 1).getValues().findIndex(x => String(x[0]) === d.aadhaar);
      if (i >= 0) r = i + 2;
    }
    sh.getRange(r, 1, 1, row.length).setNumberFormat('@').setValues([row]);
    return out_(true);
  } catch (err) {
    return out_(false, 'Server error: ' + err.message);
  } finally {
    lock.releaseLock();
  }
}

function doGet() { return ContentService.createTextOutput('Registration endpoint chal raha hai ✓'); }
function out_(ok, error) {
  return ContentService.createTextOutput(JSON.stringify({ok: ok, error: error || ''})).setMimeType(ContentService.MimeType.JSON);
}
