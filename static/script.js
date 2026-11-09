// === CLONE SUPPORT (AX_BASE খালি থাকলে original এর মতোই আচরণ) ===
const AXB = (window.AX_BASE || "");
function __axStore(real) {
    if (!AXB) return real;                       // original: কোনো বদল নয়
    const P = AXB + ":";
    return new Proxy({}, {
        get(_, p) {
            if (p === "getItem") return k => real.getItem(P + k);
            if (p === "setItem") return (k, v) => real.setItem(P + k, String(v));
            if (p === "removeItem") return k => real.removeItem(P + k);
            return undefined;
        },
        ownKeys() { return Object.keys(real).filter(k => k.startsWith(P)).map(k => k.slice(P.length)); },
        getOwnPropertyDescriptor() { return {enumerable: true, configurable: true}; }
    });
}
const LS = __axStore(window.localStorage);
const SS = __axStore(window.sessionStorage);

(function () {}());

// Anti-inspect
document.addEventListener('contextmenu', e => e.preventDefault());
document.onkeydown = function(e) {
    if (e.keyCode == 123 || (e.ctrlKey && e.shiftKey && e.keyCode == 73) || (e.ctrlKey && e.keyCode == 85)) return false;
};

// ALL EMOTES - Real Free Fire Emotes with CDN images
const CDN = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/";
const ALL_EMOTES = [
    {id:"909000075",name:"Cobra Rising"},
    {id:"909000063",name:"Ak Max"},
    {id:"909035007",name:"Shotgun Max"},
    {id:"909000068",name:"Scar Max"},
    {id:"909000085",name:"XM8 Max"},
    {id:"909038012",name:"G18 Max"},
    {id:"909035012",name:"AN94 Max"},
    {id:"909033002",name:"MP5 Max"},
    {id:"909051003",name:"M60 Max"},
    {id:"909037011",name:"Fist Max"},
    {id:"909000081",name:"M10 Max"},
    {id:"909000090",name:"Famas Max"},
    {id:"909049010",name:"P90 Max"},
    {id:"909038010",name:"Thompson Max"},
    {id:"909033001",name:"M4A1 Max"},
    {id:"909000098",name:"UMP Max"},
    {id:"909040010",name:"MP40 Max"},
    {id:"909045001",name:"Parafal Max"},
    {id:"909042008",name:"Woodpecker Max"},
    {id:"909000002",name:"LOL"},
    {id:"909000014",name:"FFWC Throne"},
    {id:"909000055",name:"I'm Rich"},
    {id:"909000060",name:"BOOYAH!"},
    {id:"909000034",name:"Pirate Flag"},
    {id:"909000010",name:"Flowers of Love"},
    {id:"909000032",name:"Selfie"},
    {id:"909000036",name:"Top DJ"},
    {id:"909000038",name:"Power of money"},
    {id:"909000039",name:"Eat my dust"},
    {id:"909000041",name:"Kungfu"},
    {id:"909000045",name:"I heart you"},
    {id:"909000046",name:"Tea Time"},
    {id:"909000052",name:"Doggie"},
    {id:"909000056",name:"Make It Rain"},
    {id:"909000058",name:"Captain Booyah"},
    {id:"909000061",name:"Bhangra"},
    {id:"909000064",name:"One Punch Man"},
    {id:"909000066",name:"Sii!"},
    {id:"909000071",name:"Cobra Dance"},
    {id:"909000074",name:"The Biker"},
    {id:"909000088",name:"Win and Chill"},
    {id:"909000089",name:"Hadouken"},
    {id:"909000135",name:"Rock Paper Scissors"},
    {id:"909000136",name:"Shattered Reality"},
    {id:"909051010",name:"On Motorbike"},
    {id:"909042012",name:"Lamborghini Ride"},
    {id:"909042007",name:"100 Gloo Sculpture"},
    {id:"909049012",name:"Open Fire"},
    {id:"909033004",name:"Drop Kick"},
    {id:"909033006",name:"BOOYAH Sparks"},
    {id:"909033010",name:"Weight of Victory"},
    {id:"909034001",name:"Chronicle Sword"},
    {id:"909034005",name:"Ridicule"},
    {id:"909034009",name:"Twerk"},
    {id:"909035001",name:"Free Money"},
    {id:"909035008",name:"Bobble Dance"},
    {id:"909036001",name:"Ghost Float"},
    {id:"909046001",name:"Aura Boarder"},
    {id:"909046006",name:"Gunspinning"},
    {id:"909046011",name:"Cant Touch This"},
    {id:"909046014",name:"Beat Drop"},
    {id:"909047001",name:"Wont Bow Down"},
    {id:"909047012",name:"JKT48 No.1"},
    {id:"909047015",name:"Rasengan"},
    {id:"909048001",name:"To the Rescue"},
    {id:"909048007",name:"Pillow Fight"},
    {id:"909048010",name:"Hit a Six"},
    {id:"909049001",name:"Nailoong Time"},
    {id:"909049018",name:"Disco Dazzle"},
    {id:"909050002",name:"Reanimation Jutsu"},
    {id:"909050005",name:"Fireball Jutsu"},
    {id:"909050006",name:"Flying Raijin"},
    {id:"909050020",name:"Sholay"},
    {id:"909051012",name:"Celestial Shot"},
    {id:"909051013",name:"Red Petals"},
    {id:"909036002",name:"Shiba Surf"},
    {id:"909036004",name:"Graffiti Cameraman"},
    {id:"909037001",name:"Reindeer Float"},
    {id:"909037002",name:"Bamboo Dance"},
    {id:"909037004",name:"Trophy Grab"},
    {id:"909037012",name:"Clap Dance"},
    {id:"909038001",name:"The Influencer"},
    {id:"909038004",name:"Be My Valentine"},
    {id:"909038011",name:"Shall We Dance"},
    {id:"909039007",name:"Grenade Magic"},
    {id:"909039010",name:"Flex"},
    {id:"909039012",name:"Fire Beast Tamer"},
    {id:"909040008",name:"Birth of Justice"},
    {id:"909040009",name:"Spider Sense"},
    {id:"909040012",name:"6th Anniv Celebration"},
    {id:"909041001",name:"Thunder Breathing"},
    {id:"909041002",name:"Water Breathing"},
    {id:"909041003",name:"Beast Breathing"},
    {id:"909041014",name:"Monster Clubbing"},
    {id:"909042001",name:"Stir-Fry Frostfire"},
    {id:"909042002",name:"Money Rain"},
    {id:"909042003",name:"Frostfire Calling"},
    {id:"909042004",name:"Stomping Foot"},
    {id:"909042005",name:"This Way"},
    {id:"909042009",name:"Celebration Schuss"},
    {id:"909042011",name:"Dawn Voyage"},
    {id:"909042013",name:"Hello Frostfire"},
    {id:"909042016",name:"Hand Grooves"},
    {id:"909042017",name:"Toiletman"},
    {id:"909042018",name:"Kemusan"},
    {id:"909043007",name:"Dragon Swipe"},
    {id:"909043008",name:"Samba"},
    {id:"909043009",name:"Speed Summon"},
    {id:"909044002",name:"The Unicyclist"},
    {id:"909044007",name:"Raise Your Thumb"},
    {id:"909044016",name:"Honk Up"},
    {id:"909045003",name:"Giddy Up"},
    {id:"909045004",name:"Goosy Dance"},
    {id:"909045005",name:"Captain Victor"},
    {id:"909045010",name:"Flower Salute"},
    {id:"909045016",name:"Naatu Naatu"},
    {id:"909045017",name:"Champions Walk"},
    {id:"909046002",name:"Booyah Champ"},
    {id:"909046003",name:"Controlled Combustion"},
    {id:"909046004",name:"Cheers to Victory"},
    {id:"909046005",name:"Shoe Shining"},
    {id:"909046007",name:"Crowd Pleaser"},
    {id:"909046008",name:"No Sweat"},
    {id:"909046009",name:"Magma Quake"},
    {id:"909046010",name:"Max Firepower"},
    {id:"909046012",name:"Firestarter"},
    {id:"909046013",name:"Flag Flair"},
    {id:"909046015",name:"Isagi Spatial"},
    {id:"909046016",name:"Nagi Trapping"},
    {id:"909046017",name:"Soaring Up"},
    {id:"909047002",name:"Aurora Iridescence"},
    {id:"909047003",name:"Couch For Two"},
    {id:"909047004",name:"Flutter Dash"},
    {id:"909047005",name:"Slippery Throne"},
    {id:"909047006",name:"Acceptance Speech"},
    {id:"909047007",name:"Love Me Not"},
    {id:"909047008",name:"Scissor Savvy"},
    {id:"909047009",name:"The Thinker"},
    {id:"909047019",name:"Clone Jutsu"},
    {id:"909048002",name:"Midnight Peruse"},
    {id:"909048003",name:"Guitar Groove"},
    {id:"909048004",name:"Keyboard Player"},
    {id:"909048005",name:"On Drums"},
    {id:"909048006",name:"Chac Chac"},
    {id:"909048009",name:"Goofy Camel"},
    {id:"909048011",name:"Flag Summon"},
    {id:"909048014",name:"Slurp Slurp"},
    {id:"909048015",name:"Sketching"},
    {id:"909048016",name:"Half Time Chilling"},
    {id:"909048017",name:"Throw In"},
    {id:"909049002",name:"Hand Raise"},
    {id:"909049003",name:"Kick It Up"},
    {id:"909049006",name:"Creation Days"},
    {id:"909049007",name:"Raining Coins"},
    {id:"909049008",name:"Clap Clap Hooray"},
    {id:"909049009",name:"Infinite Loops"},
    {id:"909049011",name:"Boxing Machine"},
    {id:"909049013",name:"Comic Barf"},
    {id:"909049016",name:"Spear Spin"},
    {id:"909049017",name:"Flag Wave"},
    {id:"909050003",name:"Final Battle"},
    {id:"909050008",name:"Hammer Slam"},
    {id:"909050009",name:"The Rings"},
    {id:"909050010",name:"Drum Twirl"},
    {id:"909050011",name:"Bunny Action"},
    {id:"909050012",name:"Broom Swoosh"},
    {id:"909050013",name:"Blade Heart"},
    {id:"909050017",name:"Bunny Wiggle"},
    {id:"909050018",name:"Flaming Heart"},
    {id:"909050019",name:"Rain or Shine"},
    {id:"909050021",name:"Peak Points"},
    {id:"909050027",name:"Boat Aura"},
    {id:"909050028",name:"Boat Rowing"},
    {id:"909051001",name:"Prismatic Flight"},
    {id:"909051002",name:"Name Not Found"},
    {id:"909051004",name:"Shower Time"},
    {id:"909000003",name: "Provoke"},
    {id:"909000057",name: "Dust Off"},
    {id:"909000062",name: "Piece of Cake"},
    {id:"909000065",name: "The Victor"},
    {id:"909000067",name: "Obliteration"},
    {id:"909000069",name: "Top Scorer"},
    {id:"909000070",name: "Triple Kicks"},
    {id:"909000072",name: "Predator Pulse"},
    {id:"909000073",name: "Ground Punch"},
    {id:"909000076",name: "One-Finger Pushup"},
    {id:"909000077",name: "Stage Time"},
    {id:"909000078",name: "Booyah! Balloon"},
    {id:"909000079",name: "More Practice"},
    {id:"909000080",name: "FFWS 2021"},
    {id:"909000086",name: "Mythos Four"},
    {id:"909000087",name: "Champion Grab"},
    {id:"909000091",name: "Big Smash"},
    {id:"909000093",name: "All In Control"},
    {id:"909000094",name: "Debugging"},
    {id:"909000095",name: "Waggor Wave"},
    {id:"909000096",name: "Crazy Guitar"},
    {id:"909000121",name: "Dribble King"},
    {id:"909000122",name: "Name Not Found"},
    {id:"909000123",name: "Mind it!"},
    {id:"909000124",name: "Golden Combo"},
    {id:"909000125",name: "Sick Moves"},
    {id:"909000128",name: "Ruler's Flag"},
    {id:"909000129",name: "Money Throw"},
    {id:"909000130",name: "Endless Bullets"},
    {id:"909000133",name: "Fire Slam"},
    {id:"909000134",name: "Heartbroken"},
    {id:"909000137",name: "Halo of Music"},
    {id:"909000138",name: "Burnt BBQ"},
    {id:"909000139",name: "Switching Steps"},
    {id:"909000140",name: "Creed Slay"},
    {id:"909000141",name: "Leap of Fail"},
    {id:"909000142",name: "Name Not Found"},
    {id:"909000143",name: "Helicopter Shot"},
    {id:"909000144",name: "Kungfu Tigers"},
    {id:"909000145",name: "Possessed Warrior"},
    {id:"909033005",name: "Sit Down!"},
    {id:"909033007",name: "The FFWS Dance"},
    {id:"909033008",name: "Easy Peasy"},
    {id:"909033009",name: "Winner Throw"},
    {id:"909034002",name: "The Collapse"},
    {id:"909034003",name: "Flaming Groove"},
    {id:"909034004",name: "Energetic"},
    {id:"909034006",name: "Tease Waggor"},
    {id:"909034007",name: "Great Conductor"},
    {id:"909034008",name: "Fake Death"},
    {id:"909034010",name: "BR-Ranked Heroic Emote"},
    {id:"909034011",name: "BR-Ranked Master Emote"},
    {id:"909034012",name: "CS-Ranked Heroic Emote"},
    {id:"909034013",name: "CS-Ranked Master Emote"},
    {id:"909034014",name: "Yes, I do"},
    {id:"909035005",name: "Victorious Eagle"},
    {id:"909035006",name: "Flying Saucer"},
    {id:"909035009",name: "Weight Training"},
    {id:"909035010",name: "Beautiful Love"},
    {id:"909035011",name: "Groove Moves"},
    {id:"909035013",name: "Louder Please"},
    {id:"909035014",name: "Ninja Stand"},
    {id:"909035015",name: "Creator In Action"},
    {id:"909036003",name: "Waiter Walk"},
    {id:"909036005",name: "Agile Boxer"},
    {id:"909036006",name: "Sunbathing"},
    {id:"909036008",name: "Skateboard Swag"},
    {id:"909036009",name: "Phantom Tamer"},
    {id:"909036010",name: "The Signal"},
    {id:"909036011",name: "Eternal Descent"},
    {id:"909036012",name: "Swaggy Dance"},
    {id:"909036014",name: "Admire"},
    {id:"909037003",name: "Dance of Constellation"},
    {id:"909037005",name: "Starry Hands"},
    {id:"909037006",name: "Yum"},
    {id:"909037007",name: "Happy Dancing"},
    {id:"909037008",name: "Juggle"},
    {id:"909037009",name: "Neon Sign"},
    {id:"909037010",name: "Beast Tease"},
    {id:"909038002",name: "Name Not Found"},
    {id:"909038003",name: "Techno Blast"},
    {id:"909038005",name: "Angry Walk"},
    {id:"909038006",name: "Make Some Noise"},
    {id:"909038008",name: "Croco Hooray"},
    {id:"909038009",name: "Scorpio Spin"},
    {id:"909038013",name: "Spin Master"},
    {id:"909039001",name: "Festival Celebration"},
    {id:"909039002",name: "Artistic Musical Dance"},
    {id:"909039003",name: "Forward, Backward"},
    {id:"909039004",name: "Scorpion Friend"},
    {id:"909039005",name: "Aching Power"},
    {id:"909039006",name: "Earthly Force"},
    {id:"909039008",name: "Oh Yeah!"},
    {id:"909039009",name: "Grace On Wheels"},
    {id:"909039011",name: "Crimson Doom"},
    {id:"909039013",name: "Crimson Tunes"},
    {id:"909039014",name: "Swaggy V-Steps"},
    {id:"909040001",name: "The Chromatic Finish"},
    {id:"909040002",name: "Smash the Feather"},
    {id:"909040003",name: "Sonorous Steps"},
    {id:"909040004",name: "Fishing for Wisdom"},
    {id:"909040005",name: "Chromatic Pop Dance"},
    {id:"909040006",name: "Chroma Twist Twist"},
    {id:"909040011",name: "Play With Thunderbolt"},
    {id:"909040013",name: "Wisdom Swing"},
    {id:"909040014",name: "Helicopter Shot"},
    {id:"909041004",name: "Flying Ink Sword"},
    {id:"909041005",name: "Diz My Popblaster"},
    {id:"909041006",name: "Dance Puppet, Dance!"},
    {id:"909041007",name: "High Knees"},
    {id:"909041008",name: "Bony Fumes"},
    {id:"909041009",name: "Feel the Electricity"},
    {id:"909041010",name: "Whac-A-Cotton"},
    {id:"909041011",name: "Honorable Mention Emote"},
    {id:"909041012",name: "BR-Ranked Grandmaster Emote"},
    {id:"909041013",name: "CS-Ranked Grandmaster Emote"},
    {id:"909041015",name: "Basudara Dance"},
    {id:"909042006",name: "Excellent Service"},
    {id:"909043001",name: "Ribbit Rider"},
    {id:"909043002",name: "Inner Self Mastery"},
    {id:"909043003",name: "Emperor's Treasure Machine"},
    {id:"909043004",name: "Why So Chaos?"},
    {id:"909043005",name: "Huge Feast"},
    {id:"909043006",name: "Color Burst"},
    {id:"909043010",name: "What a Match"},
    {id:"909043013",name: "What a Pair"},
    {id:"909044001",name: "Byte Mounting"},
    {id:"909044003",name: "Basket Rafting"},
    {id:"909044004",name: "Happy Lamb Shouldering"},
    {id:"909044005",name: "Paradox of Enlightenment"},
    {id:"909044006",name: "Harmonious Paradox"},
    {id:"909044015",name: "The Final Paradox"},
    {id:"909045002",name: "Spring Rocker"},
    {id:"909045011",name: "Little Foxy Run"},
    {id:"909045012",name: "Mr. Waggor's Seesaw"},
    {id:"909045015",name: "Floating Meditation"},
    {id:"909050065",name: "fireborn"},
    {id:"909000020",name: "devilsmove"},
    {id:"909000023",name: "emote_22"},
    {id:"909000012",name: "pushup"},
    {id:"909000015",name: "dragonfist"},
    {id:"909000011",name: "mummydance"},
    {id:"909000006",name: "chicken"},
    {id:"909000008",name: "shootdance"},
    {id:"909000017",name: "jaguardance"},
    {id:"909000027",name: "gloriousspin"},
    {id:"909000005",name: "dab"},
    {id:"909000021",name: "emote_31"},
    {id:"909000040",name: "emote_33"},
    {id:"909000024",name: "puffyride"},
    {id:"909000025",name: "petals"},
    {id:"909051006",name: "emote_37"},
    {id:"909051008",name: "emote_38"},
    {id:"909051005",name: "emote_40"},
    {id:"909000048",name: "whyohwhy"},
    {id:"909044012",name: "zombified"},
    {id:"909048008",name: "targetpractice"},
    {id:"909047010",name: "matchcountdown"},
    {id:"909050014",name: "mapread"},
    {id:"909051016",name: "emote_78"},
    {id:"909050030",name: "emote_79"},
    {id:"909050029",name: "emote_80"},
    {id:"909050015",name: "tomato"},
    {id:"909049004",name: "slapandtwist"},
    {id:"909050004",name: "foreheadpoke"},
    {id:"909000001",name: "hi"},
    {id:"909000004",name: "applause"},
    {id:"909000007",name: "armwave"},
    {id:"909000009",name: "babyshark"},
    {id:"909000013",name: "shuffling"},
    {id:"909000016",name: "dangerousgame"},
    {id:"909000018",name: "threaten"},
    {id:"909000019",name: "shakewithme"},
    {id:"909000022",name: "moonflip"},
    {id:"909000026",name: "shakeitup"},
    {id:"909000028",name: "cranekick"},
    {id:"909000031",name: "jigdance"},
    {id:"909000033",name: "soulshaking"},
    {id:"909000035",name: "healingdance"},
    {id:"909000037",name: "deathglare"},
    {id:"909000042",name: "bonappetit"},
    {id:"909000043",name: "aimfire"},
    {id:"909000044",name: "swan"},
    {id:"909000047",name: "bringiton"},
    {id:"909000049",name: "fancyhands"},
    {id:"909000051",name: "shimmy"},
    {id:"909000053",name: "challengeon"},
    {id:"909000054",name: "lasso"},
    {id:"909000059",name: "emote_138"},
    {id:"909000082",name: "goodgame"},
    {id:"909000083",name: "greetings"},
    {id:"909000084",name: "walker"},
    {id:"909000126",name: "rapswag"},
    {id:"909000127",name: "battleinstyle"},
    {id:"909000131",name: "smoothsway"},
    {id:"909000132",name: "number1"},
    {id:"909000150",name: "raiseyourthumb"},
    {id:"909033003",name: "comeanddance"},
    {id:"909044008",name: "claphands"},
    {id:"909044009",name: "donedeal"},
    {id:"909044010",name: "starcatcher"},
    {id:"909044011",name: "paradoxwings"},
    {id:"909045006",name: "youknowimgood"},
    {id:"909045007",name: "stepstep"},
    {id:"909045008",name: "superyay"},
    {id:"909045009",name: "moonwalk"},
    {id:"909047011",name: "hiptwists"},
    {id:"909047013",name: "stormyascent"},
    {id:"909047017",name: "ninjasign"},
    {id:"909047018",name: "ninjarun"},
    {id:"909048012",name: "swiftsteps"},
    {id:"909048013",name: "carnivalfunk"},
    {id:"909048018",name: "bailalorocky"},
    {id:"909048019",name: "emote_332"},
    {id:"909048020",name: "emote_333"},
    {id:"909048021",name: "emote_334"},
    {id:"909050016",name: "tacticalmoveout"},
    {id:"909051007",name: "c1"},
    {id:"909051009",name: "c2"},
    {id:"909051011",name: "c3"},
    {id:"909051017",name: "c4"},
    {id:"909051018",name: "c5"},
    {id:"909051019",name: "c6"},
    {id:"909051020",name: "c7"},
    {id:"909052004",name: "c8"},
    {id:"909052002",name: "c9"},
    {id:"909052005",name: "c10"},
    {id:"909052007",name: "c11"},
    {id:"909052006",name: "c12"},
    {id:"909052001",name: "c13"},
    {id:"909052008",name: "c14"},
    {id:"909052012",name: "c15"},
    {id:"909052010",name: "c16"},
    {id:"909052011",name: "husky"},
    {id:"909052003",name: "marching"},
    {id:"909052009",name: "summoning"},
    {id:"909052013",name: "parafal"},
    {id:"909052014",name: "prime"},
    {id:"909052015",name: "p1"},
    {id:"909052016",name: "p2"},
    {id:"909049005",name: "p3"},
    {id:"909049014",name: "new4"},
    {id:"909049015",name: "new5"},
    {id:"909049019",name: "new9"},
    {id:"909049020",name: "new10"},
    {id:"909049021",name: "new11"},
].map(e => ({...e, img: CDN + e.id + ".png"}));

const DIRECT_LINKS = [];
let completedTasks = new Set();
let totalTasks = 0;

// === EXPIRY CHECK ===
function checkExpiry() {
    const unlockTime = LS.getItem("unlock_time");
    if (unlockTime && (new Date()).getTime() - parseInt(unlockTime) > 7200000) {
        LS.removeItem("is_unlocked");
        LS.removeItem("unlock_time");
        for (let key in LS) {
            if (key.startsWith("done_") || key.startsWith("clicks_")) {
                LS.removeItem(key);
            }
        }
    }
}

// === LOADING ===
function showLoading(emoteName, emoteId) {
    document.getElementById("loading-status").textContent = `Preparing to send: ${emoteName} (${emoteId})`;
    document.getElementById("loading-overlay").classList.remove("hidden");
    document.getElementById("loading-overlay").classList.remove("fade-out");
}
function hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    overlay.classList.add("fade-out");
    setTimeout(() => overlay.classList.add("hidden"), 300);
}

// === TASKS - FIXED ===
function loadTasks() {
    const taskList = document.getElementById("task-list");
    if (!taskList) {
        console.error("ERROR: task-list element not found!");
        return;
    }
    
    console.log("Loading tasks from /api/tasks...");
    
    // Show loading state
    taskList.innerHTML = `<div class="task-btn" style="pointer-events:none;"><i class="fas fa-spinner fa-spin"></i> Loading...</div>`;
    
    fetch(AXB + '/api/tasks')
        .then(r => {
            console.log("Tasks API response status:", r.status);
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(tasks => {
            console.log("Tasks loaded:", tasks);
            taskList.innerHTML = "";
            totalTasks = tasks.length;
            completedTasks.clear();
            
            if (!tasks || tasks.length === 0) {
                taskList.innerHTML = `<div class="task-btn" style="pointer-events:none;color:#888;">No tasks available</div>`;
                totalTasks = 0;
                return;
            }
            
            tasks.forEach(task => {
                const isDone = LS.getItem("done_" + task.id);
                if (isDone) {
                    completedTasks.add(task.id);
                    taskList.innerHTML += `<div class="task-btn task-done" style="pointer-events:none;"><i class="fas fa-check-circle"></i> ${task.name} - Completed</div>`;
                } else {
                    taskList.innerHTML += `<div class="task-btn" id="task-${task.id}" onclick="handleTaskClick('${task.id}','${task.link}')"><i class="fab fa-telegram"></i> ${task.name}</div>`;
                }
            });
        })
        .catch(err => {
            console.error("Failed to load tasks:", err);
            // Fallback: show default task
            taskList.innerHTML = `<div class="task-btn" onclick="handleTaskClick('task1','https://t.me/axemoteserver')"><i class="fab fa-telegram"></i> JOIN TELEGRAM CHANNEL</div>`;
            totalTasks = 1;
        });
}

function handleTaskClick(taskId, link) {
    console.log("Task clicked:", taskId, "Link:", link);
    LS.setItem("done_" + taskId, "true");
    window.open(link, "_blank");
    setTimeout(loadTasks, 300);
}

// === STATUS CHECK ===
function checkStatus() {
    fetch(AXB + '/api/settings')
        .then(r => r.json())
        .then(settings => {
            if (settings.no_tasks) window.AX_NO_TASKS = true;
            if (settings.maintenance === "on") {
                document.getElementById("maintenance-overlay").classList.remove("hidden");
                const btn = document.getElementById("maint-telegram-btn");
                if (btn && settings.telegram) btn.href = settings.telegram;
                const overlay = document.getElementById("maintenance-overlay");
                const heading = overlay.querySelector("h2"); if (heading && settings.notice) heading.textContent = settings.notice;
                const old = document.getElementById("maint-social-links"); if (old) old.remove();
                if (settings.social_links && settings.social_links.length) {
                    const box=document.createElement("div"); box.id="maint-social-links"; box.style.cssText="width:100%;display:flex;flex-direction:column;gap:10px;margin-top:12px";
                    settings.social_links.forEach(x=>{if(!x.link)return;const a=document.createElement("a");a.className="task-btn";a.textContent=x.name;a.href=x.link;a.target="_blank";a.rel="noopener";box.appendChild(a);}); overlay.appendChild(box);
                }
            } else {
                document.getElementById("maintenance-overlay").classList.add("hidden");
                checkLock();
            }
        })
        .catch(() => checkLock());
}

// === LOCK CHECK ===
function checkLock() {
    if (window.AX_NO_TASKS) {                       // clone: কোনো টাস্ক নেই → সরাসরি main UI
        showMainUI();
        return;
    }
    if (LS.getItem("is_unlocked") === "true") {
        document.getElementById("lock-overlay").classList.add("hidden");
        showMainUI();
    } else {
        document.getElementById("lock-overlay").classList.remove("hidden");
        document.getElementById("main-container").style.display = "none";
        loadTasks();
    }
}

// === MAIN UI (task complete হলে সরাসরি এখানে আসে) ===
function showMainUI() {
    document.getElementById("lock-overlay").classList.add("hidden");
    document.getElementById("main-container").style.display = "block";
    loadServers();
    loadVisitCount();
    if (!window.__botPoll) window.__botPoll = setInterval(refreshBots, 5000);
}

// === VISIT COUNT ===
function loadVisitCount() {
    fetch(AXB + '/api/visits')
        .then(r => r.json())
        .then(data => {
            const el = document.getElementById("visit-count-box");
            if (el) {
                el.innerHTML = `<span><i class="fas fa-users"></i> Total: <b>${data.total}</b></span>
                                <span><i class="fas fa-calendar-day"></i> আজ: <b>${data.today}</b></span>`;
            }
        })
        .catch(() => {});
}

// === BOT START ===
document.addEventListener("DOMContentLoaded", function () {
    checkExpiry();

    // VERIFY BUTTON
    const unlockBtn = document.getElementById("check-unlock-btn");
    if (unlockBtn) {
        unlockBtn.addEventListener("click", () => {
            fetch(AXB + '/api/tasks')
                .then(r => r.json())
                .then(tasks => {
                    let doneCount = 0;
                    tasks.forEach(t => { if (LS.getItem("done_" + t.id)) doneCount++; });
                    if (doneCount >= tasks.length && tasks.length > 0) {
                        LS.setItem("is_unlocked", "true");
                        LS.setItem("unlock_time", (new Date()).getTime().toString());
                        showMainUI();
                    } else {
                        alert("সবগুলো টাস্ক আগে সম্পন্ন করুন!");
                    }
                })
                .catch(() => {
                    LS.setItem("is_unlocked", "true");
                    LS.setItem("unlock_time", (new Date()).getTime().toString());
                    showMainUI();
                });
        });
    }

    // UID INPUTS
    const uContainer = document.getElementById("uid-container");
    if (uContainer) {
        for (let i = 1; i <= 5; i++) {
            uContainer.innerHTML += `<div class="input-box" style="margin-bottom:10px;">
                <input type="text" id="uid${i}" placeholder="UID ${i} ${i == 1 ? '[REQUIRED]' : ''}" oninput="saveData('uid${i}',this.value)">
                <i class="fas fa-paste paste-icon" onclick="pasteText('uid${i}')"></i>
            </div>`;
        }
        for (let i = 1; i <= 5; i++) {
            const el = document.getElementById(`uid${i}`);
            if (el) el.value = LS.getItem(`uid${i}`) || "";
        }
    }

    const tcInput = document.getElementById("team-code");
    if (tcInput) {
        tcInput.value = LS.getItem("tc") || "";
        tcInput.oninput = e => saveData("tc", e.target.value);
    }

    const eList = document.getElementById("emote-list");
    if (eList) {
        ALL_EMOTES.forEach(e => {
            eList.innerHTML += `<div class="emote-item" onclick="send('${e.id}','${e.name}',this)">
                <img src="${e.img}" loading="lazy" alt="${e.name}" onerror="this.src='https://i.ibb.co/XS7p2QT/emote.png'">
                <p>${e.name}</p>
            </div>`;
        });
    }

    checkStatus();
});

// === SERVER -> BOT SELECT (dropdown: ক্লিকে সব দেখায়, সিলেক্ট করলে শুধু সেটা থাকে) ===
let SEL_SERVER = null;   // {id, name}
let API_MODE = false;
let JSON_MODE = false;
let SERVER_MODES = {};
let SEL_BOT = null;      // {id, name}
let SERVER_CACHE = [];
let BOT_CACHE = [];

function escHtml(t) { return String(t == null ? "" : t).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }

function setDD(which, open) {
    const dd = document.getElementById(which + "-dd");
    if (dd) dd.classList.toggle("open", !!open);
}
function toggleDD(which) {
    const dd = document.getElementById(which + "-dd");
    if (!dd) return;
    const willOpen = !dd.classList.contains("open");
    setDD("server", false); setDD("bot", false);
    setDD(which, willOpen);
    if (willOpen) { which === "server" ? loadServers() : refreshBots(); }
}
document.addEventListener("click", e => {
    if (!e.target.closest(".dd")) { setDD("server", false); setDD("bot", false); }
});

function loadServers() {
    const container = document.getElementById("server-list-container");
    if (!container) return;
    fetch(AXB + '/api/servers', {cache: "no-store"})
        .then(r => r.json())
        .then(servers => {
            SERVER_CACHE = servers;
            container.innerHTML = "";
            if (!servers.length) {
                container.innerHTML = `<div class="dd-empty">কোনো সার্ভার নেই</div>`;
            }
            servers.forEach(s => {
                const item = document.createElement("div");
                item.className = "dd-item" + (SEL_SERVER && SEL_SERVER.id === s.id ? " active" : "");
                const showCounts = (s.mode || 'manual') === 'manual';
                item.innerHTML = `<span class="dd-name">${escHtml(s.name)}</span><span class="dd-count">${showCounts?`${s.online}/${s.total}`:''}</span>`;
                item.onclick = (ev) => { ev.stopPropagation(); selectServer(s); };
                container.appendChild(item);
            });
            // আগের সিলেকশন ফিরিয়ে আনো
            const saved = SS.getItem("sel_server");
            if (saved && !SEL_SERVER) {
                const f = servers.find(x => x.id === saved);
                if (f) selectServer(f, true);
            }
            // সিলেক্ট করা সার্ভার ডিলিট হয়ে গেলে
            if (SEL_SERVER && !servers.find(x => x.id === SEL_SERVER.id)) resetServer();
            if (API_MODE) refreshApiStatus();
        })
        .catch(() => { container.innerHTML = `<div class="dd-empty">সার্ভার লোড হয়নি</div>`; });
}

function selectServer(s, silent) {
    const changed = !SEL_SERVER || SEL_SERVER.id !== s.id;
    SEL_SERVER = {id: s.id, name: s.name};
    const mode = SERVER_MODES[s.id] || 'manual'; API_MODE = mode === 'api' || mode === 'json'; JSON_MODE = mode === 'json';
    SS.setItem("sel_server", s.id);
    document.getElementById("server-trigger-text").textContent = s.name;
    document.getElementById("server-trigger").classList.add("chosen");
    setDD("server", false);                       // বাকি সব সার্ভার লুকিয়ে যাবে
    document.getElementById("bot-card").style.display = API_MODE ? "none" : "block";
    const runBtn = document.getElementById("save-server-btn");
    const statusBox = document.getElementById("save-server-status");
    if (runBtn) runBtn.style.display = API_MODE ? "block" : "none";
    if (statusBox) statusBox.style.display = API_MODE ? "block" : "none";
    if (changed) {
        SEL_BOT = null; SS.removeItem("sel_bot");
        document.getElementById("bot-trigger-text").textContent = "SELECT BOT";
        document.getElementById("bot-trigger").classList.remove("chosen");
        updateBotBar();
    }
    loadServerHighlight();
    if (API_MODE) refreshApiStatus(); else refreshBots();
}

function loadServerHighlight() {
    document.querySelectorAll("#server-list-container .dd-item").forEach((el, i) => {
        const s = SERVER_CACHE[i];
        el.classList.toggle("active", !!(s && SEL_SERVER && s.id === SEL_SERVER.id));
    });
}

function resetServer() {
    SEL_SERVER = null; SEL_BOT = null;
    SS.removeItem("sel_server"); SS.removeItem("sel_bot");
    document.getElementById("server-trigger-text").textContent = "SELECT SERVER";
    document.getElementById("server-trigger").classList.remove("chosen");
    document.getElementById("bot-card").style.display = "none";
    const runBtn = document.getElementById("save-server-btn"); if (runBtn) runBtn.style.display = (API_MODE && !!SEL_SERVER) ? "block" : "none";
    const logoutBtn = document.getElementById("logout-server-btn"); if (logoutBtn) logoutBtn.style.display = "none";
    const statusBox = document.getElementById("save-server-status"); if (statusBox) { statusBox.style.display = API_MODE ? "block" : "none"; if(API_MODE) statusBox.textContent = "SELECT A SERVER"; }
    updateBotBar();
}

function refreshBots() {
    if (!SEL_SERVER || API_MODE) return;
    fetch(AXB + '/api/bots?server=' + encodeURIComponent(SEL_SERVER.id), {cache: "no-store"})
        .then(r => r.json())
        .then(bots => {
            BOT_CACHE = bots;
            const box = document.getElementById("bot-list-container");
            if (!box) return;
            // সিলেক্ট করা bot ডিলেট হয়ে গেলে সিলেকশন মুছে যাবে
            if (SEL_BOT && !bots.find(b => b.id === SEL_BOT.id)) {
                SEL_BOT = null; SS.removeItem("sel_bot");
            }
            if (!SEL_BOT) {
                const sb = SS.getItem("sel_bot");
                const f = sb && bots.find(b => b.id === sb);
                if (f) SEL_BOT = {id: f.id, name: f.name};
            }
            // trigger এ শুধু সিলেক্ট করা bot দেখাবে
            const txt = document.getElementById("bot-trigger-text");
            const trig = document.getElementById("bot-trigger");
            if (SEL_BOT) {
                const cur = bots.find(b => b.id === SEL_BOT.id);
                const on = cur && cur.status === "online";
                txt.innerHTML = `${escHtml(SEL_BOT.name)} <span class="dd-badge ${on ? "on" : "off"}">${on ? "ONLINE" : "OFFLINE"}</span>`;
                trig.classList.add("chosen");
            } else {
                txt.textContent = "SELECT BOT"; trig.classList.remove("chosen");
            }
            // dropdown list (খুললে সব bot দেখাবে)
            if (!bots.length) {
                box.innerHTML = `<div class="dd-empty">এই সার্ভারে কোনো bot নেই</div>`;
            } else {
                box.innerHTML = "";
                bots.forEach(b => {
                    const on = b.status === "online";
                    const item = document.createElement("div");
                    item.className = "dd-item" + (SEL_BOT && SEL_BOT.id === b.id ? " active" : "") + (on ? "" : " disabled");
                    item.innerHTML = `<span class="dd-name"><i class="fas fa-robot"></i> ${escHtml(b.name)}</span>
                                      <span class="dd-badge ${on ? "on" : "off"}">${on ? "ONLINE" : "OFFLINE"}</span>`;
                    item.onclick = (ev) => {
                        ev.stopPropagation();
                        if (!on) { alert("এই bot এখন Offline — অন্য bot সিলেক্ট করুন"); return; }
                        SEL_BOT = {id: b.id, name: b.name};
                        SS.setItem("sel_bot", b.id);
                        setDD("bot", false);          // বাকি সব bot লুকিয়ে যাবে
                        refreshBots();
                    };
                    box.appendChild(item);
                });
            }
            updateBotBar(bots);
        })
        .catch(() => {});
}

function updateBotBar(bots) {
    const nameEl = document.getElementById("display-bot-name");
    const badge = document.getElementById("bot-online-badge");
    if (!nameEl || !badge) return;
    if (!SEL_BOT) { nameEl.textContent = "NOT SELECTED"; badge.textContent = "—"; badge.className = "bot-badge off"; return; }
    nameEl.textContent = SEL_BOT.name;
    const cur = bots && bots.find(b => b.id === SEL_BOT.id);
    const on = cur ? cur.status === "online" : false;
    badge.textContent = on ? "ONLINE" : "OFFLINE";
    badge.className = "bot-badge " + (on ? "on" : "off");
}

function saveData(k, v) { LS.setItem(k, v); }

async function pasteText(id) {
    try {
        const text = await navigator.clipboard.readText();
        document.getElementById(id).value = text;
        saveData(id, text);
    } catch (e) { alert("Clipboard permission needed!"); }
}

function logTerm(m, c = "#00ff88") {
    const content = document.getElementById("terminal-content");
    const term = document.getElementById("terminal");
    term.style.display = "block";
    const line = document.createElement("div");
    line.className = "terminal-line";
    line.style.color = c;
    line.innerHTML = `> ${m}`;
    content.appendChild(line);
    term.scrollTop = term.scrollHeight;
}


async function initApiMode(){
    try {
        const r = await fetch(AXB + '/api/runtime-config', {cache:'no-store'});
        const d = await r.json(); SERVER_MODES = d.server_modes || {}; API_MODE = d.auth_mode === 'api' || d.auth_mode === 'json'; JSON_MODE = d.auth_mode === 'json';
        const botCard=document.getElementById('bot-card'), botBar=document.getElementById('bot-status-bar');
        if (API_MODE) { if(botCard)botCard.style.display='none'; if(botBar)botBar.style.display='none'; }
        else { if(botBar)botBar.style.display='flex'; }
        loadServers();
        if(API_MODE) { setTimeout(refreshApiStatus,500); if(!window.__axApiPoll) window.__axApiPoll=setInterval(refreshApiStatus,3000); }
    } catch(e) {}
}
async function refreshApiStatus(){
    if(!API_MODE) return;
    const status=document.getElementById('save-server-status'), runBtn=document.getElementById('save-server-btn'), logoutBtn=document.getElementById('logout-server-btn');
    try {
        const r=await fetch(AXB+'/api/my-bot',{cache:'no-store'}), d=await r.json();
        if(d.active){
            const server=SERVER_CACHE.find(x=>x.id===d.server_id);
            if(server){ SEL_SERVER={id:server.id,name:server.name}; document.getElementById('server-trigger-text').textContent=server.name; document.getElementById('server-trigger').classList.add('chosen'); }
            if(status){ status.style.display='block'; status.innerHTML=['online','running','connected','success','ready'].includes(String(d.status||'').toLowerCase()) ? '<strong style="color:#20d66b">BOT CONNECT ✅</strong>' : '<strong style="color:#f0c000">BOT CONNECTING...</strong>';  }
            if(runBtn) runBtn.style.display='none'; if(logoutBtn) logoutBtn.style.display='block';
        } else {
            if(status){status.style.display=API_MODE?'block':'none';status.textContent=SEL_SERVER?'SERVER SELECTED — PRESS START BOT':'SELECT A SERVER';}
            if(runBtn){runBtn.style.display=API_MODE && !!SEL_SERVER?'block':'none';runBtn.textContent='START BOT';runBtn.disabled=false;}
            if(logoutBtn) logoutBtn.style.display='none';
        }
    } catch(e) { if(status){status.style.display='block';status.textContent='BOT STATUS UNAVAILABLE — REFRESH PAGE';} }
}
async function runSelectedServer(){
    if(!SEL_SERVER){alert('আগে SERVER সিলেক্ট করুন!');return;}
    const btn=document.getElementById('save-server-btn'), status=document.getElementById('save-server-status');
    btn.disabled=true; btn.textContent='STARTING...'; status.style.display='block'; status.textContent='BOT STARTING... PLEASE WAIT';
    try {
        const r=await fetch(AXB+'/api/save-server',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({server_id:SEL_SERVER.id})});
        const d=await r.json(); if(!d.ok) throw new Error(d.error||'Server start failed');
        status.textContent='BOT CONNECTING...';
        btn.style.display='none'; document.getElementById('logout-server-btn').style.display='block';
        [1200,2500,4500,7000,10000].forEach(ms=>setTimeout(refreshApiStatus,ms));
    } catch(e) { status.textContent='BOT START FAILED — TRY AGAIN'; btn.textContent='START BOT'; btn.disabled=false; }
}
async function logoutApiBot(){
    const btn=document.getElementById('logout-server-btn'), status=document.getElementById('save-server-status');
    btn.disabled=true; btn.textContent='LOGGING OUT...';
    try {
        const r=await fetch(AXB+'/api/logout-bot',{method:'POST'}); const d=await r.json();
        if(!d.ok) throw new Error(d.error||'Logout failed');
        status.textContent='BOT LOGGED OUT — SELECT A SERVER';
        btn.style.display='none'; btn.disabled=false; btn.textContent='LOGOUT BOT';
        const run=document.getElementById('save-server-btn'); run.style.display=SEL_SERVER?'block':'none'; run.disabled=false; run.textContent='START BOT';
        if(SEL_SERVER){ SEL_SERVER=null; document.getElementById('server-trigger-text').textContent='SELECT SERVER'; document.getElementById('server-trigger').classList.remove('chosen'); }
    } catch(e){status.textContent='LOGOUT FAILED — TRY AGAIN';btn.disabled=false;btn.textContent='LOGOUT BOT';}
}
const _runServerButton=document.getElementById('save-server-btn'); if(_runServerButton)_runServerButton.addEventListener('click',runSelectedServer);
const _logoutServerButton=document.getElementById('logout-server-btn'); if(_logoutServerButton)_logoutServerButton.addEventListener('click',logoutApiBot);

function send(id, name, el) {
    document.querySelectorAll(".emote-item").forEach(i => i.classList.remove("selected"));
    el.classList.add("selected");

    const tc = document.getElementById("team-code").value;
    const uid1 = document.getElementById("uid1").value;

    if (!SEL_SERVER) { alert("আগে SERVER সিলেক্ট করুন!"); return; }
    if (!API_MODE && !SEL_BOT) { alert("একটি BOT সিলেক্ট করুন!"); return; }
    if (!tc || !uid1) { alert("Team Code এবং UID 1 দিন!"); return; }

    showLoading(name, id);
    document.getElementById("terminal-content").innerHTML = "";
    logTerm("CONNECTING...");

    let url = API_MODE
        ? `${AXB}/join?server=${encodeURIComponent(SEL_SERVER.id)}&tc=${tc}`
        : `${AXB}/join?bot=${encodeURIComponent(SEL_BOT.id)}&tc=${tc}`;
    for (let i = 1; i <= 5; i++) {
        const v = document.getElementById(`uid${i}`).value;
        if (v) url += `&uid${i}=${v}`;
    }
    url += `&emote_id=${id}`;

    fetch(url).then(r => r.json().catch(() => ({}))).then(d => {
        setTimeout(() => {
            if (d && d.status === "error") logTerm(`ERROR: ${d.message || "failed"}`, "red");
            else logTerm(API_MODE ? `SENT: ${name} [${id}] via API BOT` : `SENT: ${name} [${id}] via ${SEL_BOT.name}`, "#00ff88");
            hideLoading();
            refreshBots();
        }, 1000);
    }).catch(() => {
        logTerm("FAILED!", "red");
        hideLoading();
    });
}

initApiMode();
