// Репозиторий для кнопки лайка. Определяется автоматически на owner.github.io/repo, либо впишите вручную: 'owner/repo'
const REPO = (() => {
    const m = location.hostname.match(/^(.+)\.github\.io$/);
    return m ? m[1] + '/' + (location.pathname.split('/')[1] || location.hostname) : 'qvp/vk_search'
})();
const $ = id => document.getElementById(id);
const S = {sex: '', from: '', to: '', cities: []};
let seen = new Set(), citiesData = null, citiesLoading = null, cur = null;

/* ---------- IndexedDB ---------- */
const dbp = new Promise((res, rej) => {
    const r = indexedDB.open('vksearch', 1);
    r.onupgradeneeded = () => {
        r.result.createObjectStore('kv');
        r.result.createObjectStore('seen')
    };
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error)
});
const tx = async (s, m, f) => {
    const db = await dbp;
    return new Promise((res, rej) => {
        const t = db.transaction(s, m);
        const o = f(t.objectStore(s));
        t.oncomplete = () => res(o && o.result);
        t.onerror = () => rej(t.error)
    })
};
const saveSettings = () => tx('kv', 'readwrite', s => s.put(S, 'settings')).catch(() => {
});

/* ---------- helpers ---------- */
function msg(t, err) {
    const m = $('msg');
    m.textContent = t || '';
    m.className = 'msg' + (err ? ' err' : '')
}

const keyOf = c => `${c.cityId}-${c.sex}-${c.y}-${c.m}-${c.d}`;

function fillAges() {
    for (const id of ['from', 'to']) {
        const s = $(id);
        s.innerHTML = '<option value="">—</option>';
        for (let a = 14; a <= 80; a++) s.insertAdjacentHTML('beforeend', `<option>${a}</option>`)
    }
}

function esc(s) {
    return String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]))
}

/* ---------- likes ---------- */
$('star').href = 'https://github.com/' + REPO;
fetch('https://api.github.com/repos/' + REPO).then(r => r.json()).then(j => {
    $('stars').textContent = typeof j.stargazers_count === 'number' ? j.stargazers_count : '0'
}).catch(() => {
    $('stars').textContent = '0'
});

/* ---------- cities ---------- */
function renderCities() {
    const ul = $('cities');
    ul.innerHTML = S.cities.length ? '' : '<li class="empty" style="background:none;padding:0;font-weight:400">Города не выбраны</li>';
    S.cities.forEach((c, i) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${esc(c.name)}<small>${esc(c.region || '')}</small></span>`;
        const b = document.createElement('button');
        b.className = 'del';
        b.textContent = 'Удалить';
        b.onclick = () => {
            S.cities.splice(i, 1);
            renderCities();
            saveSettings()
        };
        li.appendChild(b);
        ul.appendChild(li)
    });
}

function loadCities() {
    // Браузер сам запрашивает файл с "Accept-Encoding: gzip" и распаковывает ответ; GitHub Pages отдаёт .json в gzip. Загружается один раз.
    if (citiesData) return Promise.resolve(citiesData);
    return citiesLoading || (citiesLoading = fetch('cities.json').then(r => {
        if (!r.ok) throw 0;
        return r.json()
    }).then(d => citiesData = d).catch(e => {
        citiesLoading = null;
        throw e
    }));
}

let dd = $('dd'), items = [], hi = -1, tmr;
const norm = s => s.toLowerCase().replace(/ё/g, 'е');

function search() {
    const q = norm($('q').value.trim());
    if (!q) {
        dd.style.display = 'none';
        return
    }
    dd.style.display = 'block';
    dd.innerHTML = '<div class="n">Загрузка списка городов…</div>';
    loadCities().then(data => {
        if (norm($('q').value.trim()) !== q) return;
        const have = new Set(S.cities.map(c => c[0] || c.id));
        const ex = [], st = [], inc = [];
        for (const c of data) {
            if (have.has(c[0]) || !c[1]) continue;
            const n = norm(String(c[1]).trim());
            if (n === q) ex.push(c);
            else if (n.startsWith(q)) st.push(c);
            else if (inc.length < 200 && n.includes(q)) inc.push(c)
        }
        const byLen = (a, b) => String(a[1]).length - String(b[1]).length;
        items = ex.concat(st.sort(byLen), inc.sort(byLen)).slice(0, 10);
        hi = -1;
        dd.innerHTML = items.length ? '' : '<div class="n">Ничего не найдено</div>';
        items.forEach((c, i) => {
            const d = document.createElement('div');
            d.innerHTML = `${esc(c[1])} <small>${esc(c[2] || '')}</small>`;
            d.onmousedown = e => {
                e.preventDefault();
                pick(c)
            };
            dd.appendChild(d)
        });
    }).catch(() => {
        dd.innerHTML = '<div class="n">Не удалось загрузить cities.json</div>'
    });
}

function pick(c) {
    if (!S.cities.some(x => x.id === c[0])) S.cities.push({id: c[0], name: c[1], region: c[2] || ''});
    $('q').value = '';
    dd.style.display = 'none';
    renderCities();
    saveSettings();
}

$('q').addEventListener('input', () => {
    clearTimeout(tmr);
    tmr = setTimeout(search, 150)
});
$('q').addEventListener('focus', () => loadCities().catch(() => {
}));
$('q').addEventListener('blur', () => setTimeout(() => dd.style.display = 'none', 100));
$('q').addEventListener('keydown', e => {
    const ds = [...dd.querySelectorAll('div:not(.n)')];
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        hi = (hi + (e.key === 'ArrowDown' ? 1 : -1) + ds.length) % (ds.length || 1);
        ds.forEach((d, i) => d.classList.toggle('on', i === hi))
    } else if (e.key === 'Enter' && items.length) {
        e.preventDefault();
        pick(items[hi < 0 ? 0 : hi])
    } else if (e.key === 'Escape') dd.style.display = 'none';
});

/* ---------- link ---------- */
function renderLink() {
    const a = $('url');
    if (!cur) {
        a.hidden = true;
        $('ph').hidden = false;
        $('rem').disabled = true;
        $('rem').textContent = 'Запомнить url';
        return
    }
    const u = `https://vk.ru/friends?act=find&city_id=${cur.cityId}&sex=${cur.sex}&birth_day=${cur.d}&birth_month=${cur.m}&birth_year=${cur.y}`;
    a.href = u;
    a.innerHTML = `https://vk.ru/friends?act=find&amp;city_id=${cur.cityId}&amp;sex=<i>${cur.sex}</i>&amp;birth_day=<i>${cur.d}</i>&amp;birth_month=<i>${cur.m}</i>&amp;birth_year=<i>${cur.y}</i>`;
    a.hidden = false;
    $('ph').hidden = true;
    const done = seen.has(keyOf(cur));
    $('rem').disabled = done;
    $('rem').textContent = done ? 'Запомнено ✓' : 'Запомнить url';
}

function updateCount() {
    $('cnt').textContent = `Запомнено дней: ${seen.size}`
}

$('rem').onclick = async () => {
    if (!cur) return;
    const k = keyOf(cur);
    seen.add(k);
    await tx('seen', 'readwrite', s => s.put(1, k));
    renderLink();
    updateCount();
    msg('День сохранён — он больше не выпадет');
};

/* ---------- generation ---------- */
function generate() {
    const sex = $('sex').value, from = +$('from').value, to = +$('to').value;
    if (!S.cities.length) return msg('Добавьте хотя бы один город', 1);
    if (!sex) return msg('Выберите пол', 1);
    if (!from || !to) return msg('Укажите возраст «от» и «до»', 1);
    if (from > to) return msg('Возраст «от» не может быть больше «до»', 1);
    const t = new Date(), y = t.getFullYear(), m = t.getMonth(), d = t.getDate();
    const start = new Date(y - to, m, d), end = new Date(y - from, m, d);   // самый старший ... самый младший
    const order = [...S.cities].sort(() => Math.random() - .5);
    for (const c of order) {
        const cand = [];
        for (let x = new Date(start); x <= end; x.setDate(x.getDate() + 1)) {
            const o = {
                cityId: c.id,
                cityName: c.name,
                sex,
                y: x.getFullYear(),
                m: x.getMonth() + 1,
                d: x.getDate()
            };
            if (!seen.has(keyOf(o))) cand.push(o);
        }
        if (cand.length) {
            cur = cand[Math.floor(Math.random() * cand.length)];
            try {
                localStorage.setItem('vk_current', JSON.stringify(cur))
            } catch (e) {
            }
            renderLink();
            return msg(`${cur.cityName}, ${cur.d}.${cur.m}.${cur.y}`)
        }
    }
    msg('Все дни для выбранных городов и возраста уже просмотрены', 1);
}

$('gen').onclick = generate;

/* ---------- import / export ---------- */
$('exp').onclick = () => {
    const b = new Blob([JSON.stringify([...seen], null, 1)], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'vk-seen-days.json';
    a.click();
    URL.revokeObjectURL(a.href);
};
$('imp').onclick = () => $('file').click();
$('file').onchange = async e => {
    const f = e.target.files[0];
    e.target.value = '';
    if (!f) return;
    try {
        const arr = JSON.parse(await f.text());
        if (!Array.isArray(arr)) throw 0;
        const add = [...new Set(arr.filter(k => typeof k === 'string' && /^\d+-(male|female)-\d+-\d+-\d+$/.test(k) && !seen.has(k)))];
        await tx('seen', 'readwrite', s => {
            add.forEach(k => s.put(1, k))
        });
        add.forEach(k => seen.add(k));
        updateCount();
        renderLink();
        msg(`Импортировано новых дней: ${add.length}`);
    } catch (x) {
        msg('Не удалось прочитать файл: нужен JSON со списком дней', 1)
    }
};

/* ---------- init ---------- */
['sex', 'from', 'to'].forEach(id => $(id).addEventListener('change', () => {
    S[id] = $(id).value;
    saveSettings()
}));
(async () => {
    fillAges();
    renderCities();
    try {
        const s = await tx('kv', 'readonly', s => s.get('settings'));
        if (s) {
            Object.assign(S, s);
            $('sex').value = S.sex;
            $('from').value = S.from;
            $('to').value = S.to;
            renderCities()
        }
        seen = new Set(await tx('seen', 'readonly', s => s.getAllKeys()));
    } catch (e) {
        msg('IndexedDB недоступна — данные не сохранятся', 1)
    }
    try {
        cur = JSON.parse(localStorage.getItem('vk_current'))
    } catch (e) {
    }
    updateCount();
    renderLink();
})();
