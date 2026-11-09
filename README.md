# AX EMOTE SERVER (OB55) — Multi-Bot + Admin Panel

চালানো:  pip install -r requirements.txt  →  python main.py

- Website:       http://<your-link>/
- Admin panel:   http://<your-link>/romjan100   (password server-side যাচাই হয়, কোনো ফাইলে plain text নেই)
- Admin password বদলাতে: hosting এ env `ADMIN_PASSWORD` সেট করুন।
- Admin path বদলাতে: env `ADMIN_PATH` (যেমন /myadmin)

ফাইল:
- main.py        → website + admin API + সব bot এর supervisor
- bot_worker.py  → একটা guest bot (প্রতিটি bot আলাদা process)
- login_engine.py, xC4.py, xHeaders.py, Pb2/ → OB55 login/packet কোড

শুধু একটি ফাইল লেখা হয়: visits.json (visit counter, আগের লজিকে)। data/ ফোল্ডার, logs, token.txt, __pycache__ — কিছুই তৈরি হয় না। bot/server তালিকা memory তে থাকে।
- Server restart হলে bot/server তালিকা ফাঁকা হয় → Admin panel এর BACKUP / RESTORE (Export / Import) দিয়ে এক ক্লিকে ফিরিয়ে আনুন।
- (ঐচ্ছিক) restart এও রাখতে চাইলে hosting env: AX_STORE_FILE=/path/store.json (তখন শুধু ওই একটা ফাইল লেখা হবে)।

## 🧬 AX EMOTE BOT CLONE (Website Clone System)
Main Admin (`/romjan100`) → উপরে **🧬 AX EMOTE BOT CLONE** বাটন → `/romjan100/clones`

প্রতিটি clone এর জন্য তৈরির সময় ঠিক হয়:
- Main UI Name (ওয়েবসাইটের শিরোনাম) — নিচে ছোট করে "POWERED BY AX EMOTE SERVER"
- টাস্ক পেইজের Social Links (সর্বোচ্চ ৮টি) — অথবা "টাস্ক ছাড়া" ওয়েবসাইট
- Bot সিস্টেম: অরিজিনাল bot ব্যবহার / আলাদা নিজস্ব bot
- Clone Admin Password
- কত দিন চলবে (মেয়াদ শেষে ওয়েবসাইট ও নিজস্ব bot অটো বন্ধ) — অথবা Unlimited

URL:  `<domain>/<৫–৭ অক্ষরের random লেটার>` (যেমন /ojehyqg)
Clone Admin:  `<domain>/<slug>/admin`  (Main Admin এর "GO TO ADMIN" দিয়ে পাসওয়ার্ড ছাড়াই ঢোকা যায়)

আলাদাকরণ: clone এর নিজস্ব bot শুধু ওই clone এ; অরিজিনাল ও অন্য clone এর সাথে মেশে না।
একই Guest UID দুই জায়গায় যোগ করা যায় না। প্রতিটি bot আলাদা process — একটা crash হলে বাকিগুলো চলে।

সীমা (env দিয়ে বদলানো যায়): AX_MAX_CLONES=200, AX_MAX_BOTS_PER_CLONE=10, AX_MAX_TOTAL_BOTS=80
Clone ডেটা memory তে থাকে; restart এও রাখতে চাইলে AX_STORE_FILE env দিন (clone সহ সব সেভ হয়)।


## 🔗 Social Media / Task / Maintenance (Admin Panel)
Admin Panel → **WEBSITE TASK & MAINTENANCE** কার্ড:
- **USER TASK PAGE:** TASK ON/OFF সুইচ + "ADD TASK LINK" বাটন (নাম → লিংক → ADD); প্রতিটি টাস্ক Edit/Delete করা যায়।
  OFF করলে User টাস্ক ছাড়াই সরাসরি Main UI পায় (লিংক মুছে যায় না)।
- **MAINTENANCE:** ON/OFF সুইচ + নোটিশ; **MAINTENANCE SOCIAL MEDIA BUTTONS** এ "ADD SOCIAL MEDIA" বাটন (নাম → লিংক → ADD)।
- Original Website Maintenance ON থাকলে /maintenance পেইজে Clone Website এর বাটনগুলো **সবুজ** রঙে দেখায়।
- Clone OFF থাকলে (Clones পেইজ → EDIT): বন্ধ থাকার Notice লেখা যায় + "ADD SOCIAL MEDIA" বাটনে Social লিংক দেওয়া যায়; ইউজার এই লেখা ও বাটনগুলো দেখে।
- Add / Edit / Delete সঙ্গে সঙ্গে সেভ হয়।


## Guest Account API Mode (BD / IND)
Main Admin Panel → ORIGINAL USER WEBSITE LOGIN MODE থেকে MANUAL Guest UID/Password অথবা GUEST ACCOUNT API নির্বাচন করুন। BD এবং IND-এর API URL আলাদা করে Edit/Save করা যায়। API Mode-এ User Website-এ Server নির্বাচন করে SAVE SERVER চাপলে API থেকে `status`, `uid`, `password` যাচাই করে bot তৈরি ও login শুরু হয়; এই Mode-এ User UI-তে Select Bot দেখানো হয় না। API response-এর JWT বা access token সংরক্ষণ/ব্যবহার করা হয় না।

Clone Website (Shared বা Own bot mode) Original Website-এর বর্তমান login mode, BD/IND API URL এবং Auto Leave setting অনুসরণ করে; Clone Edit করার পরও এই নিয়ম বজায় থাকে। Login/API configuration Original Admin Panel থেকেই নিয়ন্ত্রণ করা হয়।

## Auto Leave
Admin Panel → ORIGINAL USER WEBSITE LOGIN MODE → AUTO LEAVE AFTER EMOTE থেকে ON করলে emote শেষে bot squad ছাড়ে; OFF করলে bot squad-এ থেকে যায়। Setting পরিবর্তন হলে সংশ্লিষ্ট bot process restart হয় যাতে নতুন setting কার্যকর হয়।

## API Mode: private per-browser bot sessions
- API-created Guest accounts are held only in the active browser session memory and are not added to Original/Clone bot storage or Admin Panel bot lists.
- Each browser session can run its own API bot. The bot is addressed by a private HttpOnly session cookie; other users cannot select or control it.
- Use **RUN SERVER** beside the server selector to create and start the bot. Use **LOGOUT** to stop and release it before selecting another server.
- India login now tries the version-configured MajorLogin endpoint first, then `https://loginbp.ggpolarbear.com` as a fallback. If GetLoginData fails, it retries `https://client.ind.freefiremobile.com`.


## Per-server login modes and JSON account pool

The Original Admin Panel can set each server independently to `MANUAL`, `GUEST API`, or `JSON ACCOUNT POOL`. For JSON mode, upload one JSON file per server using this format:

```json
{
  "accounts": [
    {"uid": "123456789", "password": "GUEST_PASSWORD", "name": "JSON BOT 1"},
    {"uid": "987654321", "password": "GUEST_PASSWORD", "name": "JSON BOT 2"}
  ]
}
```

The account pool is stored separately for BD and IND. Template files `guest_accounts_BD.template.json` and `guest_accounts_IND.template.json` are included; upload the relevant file after selecting its matching server in Admin. A user pressing Run Server receives one available account from the selected server pool. JSON bots appear in a separate Admin list, show the team code used, and expire 10 minutes after their worker reaches online status. Logout removes the active lease from the Admin list while keeping the account in the pool for later use. Only one active bot can claim a given team code. Admin can restart/delete one JSON bot or bulk restart/delete active JSON bots.

For persistence across server restarts, configure `AX_STORE_FILE` to a protected writable JSON file on the host. The account pool contains guest passwords; restrict filesystem and backup access.

India login uses `https://login.ind.freefiremobile.com` for MajorLogin and `https://client.ind.freefiremobile.com` for GetLoginData. BD routing remains on the existing dynamic version-config endpoint.


JSON pool persistence defaults to `json_accounts.json` (override with `AX_JSON_POOL_FILE`). This file stores Guest UID/password credentials; keep it out of public repositories and restrict host access.
