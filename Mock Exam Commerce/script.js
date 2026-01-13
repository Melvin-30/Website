// script.js — corrected & integrated version

// ================= Utility =====================
function shuffle(arr) { return Array.isArray(arr) ? [...arr].sort(() => Math.random() - 0.5) : []; }
function pickRandom(arr, n) { if (!Array.isArray(arr)) return []; return shuffle(arr).slice(0, Math.max(0, n)); }

// ================= Flexible JSON loader =====================
async function loadJSON(name) {
    try {
        const res = await fetch('questions/' + name);
        if (!res.ok) {
            console.warn('Missing JSON:', name);
            return [];
        }
        const data = await res.json();
        // accept either an array or { questions: [...] }
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.questions)) return data.questions;
        return [];
    } catch (err) {
        console.error('Error loading', name, err);
        return [];
    }
}

// ================= Load all files =====================
async function loadAll() {
    return {
        fill: await loadJSON('fillups.json'),
        tf: await loadJSON('truefalse.json'),
        mcq1: await loadJSON('mcq_single.json'),
        mcq2: await loadJSON('mcq_twocorrect.json'),
        mcq3: await loadJSON('mcq_threecorrect.json'),
        match: await loadJSON('match.json'),
        qna: await loadJSON('qna.json'),
        qna1: await loadJSON('qna1.json'),
        qna2: await loadJSON('qna2.json')
    };
}

// ================= Normalize helpers =====================
function optionTexts(q) { if (!q || !Array.isArray(q.options)) return []; return q.options.map(opt => (typeof opt === 'string' ? opt : (opt.text || opt))); }

function answerIndices(q) {
    const opts = optionTexts(q);
    const ans = q.answer;
    if (ans == null) return [];
    if (typeof ans === 'number') return [String(ans)];
    if (typeof ans === 'string') {
        const idx = opts.findIndex(o => String(o).trim() === ans.trim());
        return idx >= 0 ? [String(idx)] : [ans];
    }
    if (Array.isArray(ans)) {
        return ans.map(a => {
            if (typeof a === 'number') return String(a);
            if (typeof a === 'string') {
                const idx = opts.findIndex(o => String(o).trim() === a.trim());
                return idx >= 0 ? String(idx) : a;
            }
            return String(a);
        });
    }
    return [];
}

function indicesKey(arr) { if (!Array.isArray(arr)) return String(arr || ''); return arr.map(String).filter(x => x !== '').sort((a, b) => a.localeCompare(b)).join(','); }

// ================= Build paper config =====================
const CONFIG = { fill: 10, tf: 10, mcq1: 10, mcq2: 10, mcq3: 2, match: 1, qna: 8, qna1: 2, qna2: 2 };

// ================= Build exam =====================
async function buildPaper() {
    const all = await loadAll();
    return {
        fill: pickRandom(all.fill, CONFIG.fill),
        tf: pickRandom(all.tf, CONFIG.tf),
        mcq1: pickRandom(all.mcq1, CONFIG.mcq1),
        mcq2: pickRandom(all.mcq2, CONFIG.mcq2),
        mcq3: pickRandom(all.mcq3, CONFIG.mcq3),
        match: pickRandom(all.match, CONFIG.match),
        qna: pickRandom(all.qna, CONFIG.qna),
        qna1: pickRandom(all.qna1, CONFIG.qna1),
        qna2: pickRandom(all.qna2, CONFIG.qna2)
    };
}

// ======================================================
// SAFE PRE RENDERING
// ======================================================
function escapeForPre(s) {
    return String(s === undefined ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
function safePre(text) { return `<pre class="q-text">${escapeForPre(text)}</pre>`; }
function safePreOpt(text) { return `<pre class="opt-pre">${escapeForPre(text)}</pre>`; }

// ================= Render Left Nav & Paper =====================
let CURRENT_PAPER = null;

const SECTIONS_META = [
    { key: 'fill', title: 'Q1 Fill in the Blanks' },
    { key: 'tf', title: 'Q2 True / False' },
    { key: 'mcq1', title: 'Q3 MCQ — Single Correct Answer' },
    { key: 'mcq2', title: 'Q4 MCQ — Two Correct Answer' },
    { key: 'mcq3', title: 'Q5 MCQ — Three Correct Answer' },
    { key: 'match', title: 'Q6 Match the Following' },
    { key: 'qna', title: 'Q7 Question Answers' },
    { key: 'qna1', title: 'Q8 A Write a Program' },
    { key: 'qna2', title: '08 B Write a Program' }
];

function renderLeftNav(paper) {
    const container = document.getElementById('sectionsList');
    if (!container) return;
    container.innerHTML = '';
    SECTIONS_META.forEach(sec => {
        const arr = paper[sec.key] || [];
        const div = document.createElement('div');
        div.className = 'section-item';

        // section title (click shows section and sets header)
        const title = document.createElement('div');
        title.className = 'section-title';
        title.innerHTML = `<div class="label">${sec.title}</div><div class="count">${arr.length}</div>`;
        div.appendChild(title);

        // subboxes (5 per row controlled by CSS; script just creates boxes)
        const boxes = document.createElement('div');
        boxes.className = 'subboxes';
        arr.forEach((q, i) => {
            const box = document.createElement('div');
            box.className = 'subbox unanswered';
            box.dataset.section = sec.key;
            box.dataset.index = i;
            box.title = `${sec.title} — part ${i + 1}`;
            box.addEventListener('click', () => {
                // show section, set header, scroll to the question
                showSection(sec.key);
                setSectionHeader(sec.title);
                const anchor = document.querySelector(`.q-block[data-section="${sec.key}"][data-index="${i}"]`);
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    anchor.classList.add('highlight');
                    setTimeout(() => anchor.classList.remove('highlight'), 1300);
                }
            });
            boxes.appendChild(box);
        });

        div.appendChild(boxes);
        container.appendChild(div);

        // clicking the section-title (not subbox) shows section and sets header
        title.addEventListener('click', () => {
            showSection(sec.key);
            setSectionHeader(sec.title);
            // scroll to first question of that section if exists
            const first = document.querySelector(`.q-block[data-section="${sec.key}"]`);
            if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });

    updateNavState();
}

// Use existing right-side header if present (#rightSectionTitle). If not, create #sectionHeader
function setSectionHeader(text) {
    const rightTitleEl = document.getElementById('rightSectionTitle');
    if (rightTitleEl) {
        // Show and set provided header (the CSS default for .right-title may hide it — ensure visible)
        rightTitleEl.style.display = text ? '' : 'none';
        rightTitleEl.textContent = text || '';
        return;
    }

    // fallback: create a header inside paperArea
    const paper = document.getElementById('paperArea');
    if (!paper) return;
    let header = document.getElementById('sectionHeader');
    if (!header) {
        header = document.createElement('div');
        header.id = 'sectionHeader';
        header.style.fontSize = '20px';
        header.style.fontWeight = '700';
        header.style.marginBottom = '12px';
        header.style.color = '#222';
        paper.prepend(header);
    }
    header.textContent = text || '';
}

function renderPaper(paper) {
    CURRENT_PAPER = paper;
    renderLeftNav(paper);
    const main = document.getElementById('paperArea');
    if (!main) {
        console.error('renderPaper: #paperArea not found');
        return;
    }
    main.innerHTML = '';

    // Render sections in order; numbering restarts at 1 for each section
    SECTIONS_META.forEach(secMeta => {
        const arr = paper[secMeta.key] || [];
        if (!arr || arr.length === 0) return;

        // section group container
        const secContainer = document.createElement('div');
        secContainer.className = 'section-group';
        secContainer.dataset.section = secMeta.key;

        arr.forEach((q, i) => {
            const block = renderBlock(secMeta.key, i, q, i + 1); // displayIndex = i+1
            // mark dataset for left nav linking
            block.dataset.section = secMeta.key;
            block.dataset.index = i;
            secContainer.appendChild(block);
        });

        main.appendChild(secContainer);
    });

    // set default header to first non-empty section
    const firstNonEmpty = SECTIONS_META.find(s => (paper[s.key] || []).length > 0);
    setSectionHeader(firstNonEmpty ? firstNonEmpty.title : '');

    // show first section by default
    showSection(firstNonEmpty ? firstNonEmpty.key : SECTIONS_META[0].key);
    updateNavState();
}

/* Render a single question block.
   displayIndex is per-section index (starts at 1) */
function renderBlock(sectionKey, idx, q, displayIndex) {
    const wrapper = document.createElement('div');
    wrapper.className = 'q-block';
    wrapper.dataset.section = sectionKey;
    wrapper.dataset.index = idx;

    const indexDiv = document.createElement('div');
    indexDiv.className = 'q-index';
    indexDiv.innerText = displayIndex;

    const body = document.createElement('div');
    body.className = 'q-body';
    const qtext = document.createElement('div');
    qtext.innerHTML = safePre(q.question || ('Question ' + (idx + 1)));
    body.appendChild(qtext);

    const actions = document.createElement('div');
    actions.className = 'q-actions';

    const controlsInBody = ['mcq1', 'mcq2', 'mcq3', 'match', 'qna', 'qna1', 'qna2'].includes(sectionKey);
    function attach(node) { if (controlsInBody) body.appendChild(node); else actions.appendChild(node); }

    if (sectionKey === 'fill') {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'user-answer';
        input.dataset.answer = q.answer ?? '';
        attach(input);
        input.addEventListener('input', updateNavState);
    } else if (sectionKey === 'tf') {
        const sel = document.createElement('select');
        sel.className = 'user-answer';
        sel.dataset.answer = (q.answer ? 'True' : 'False');
        sel.innerHTML = `<option value="">Select</option><option value="True">True</option><option value="False">False</option>`;
        attach(sel);
        sel.addEventListener('change', updateNavState);
    } else if (sectionKey === 'mcq1' || sectionKey === 'mcq2' || sectionKey === 'mcq3') {
        const opts = optionTexts(q);
        const correctKey = indicesKey(answerIndices(q));
        const mcqDiv = document.createElement('div');
        mcqDiv.className = 'mcq-container';

        opts.forEach((t, i) => {
            const label = document.createElement('label');
            label.className = 'mcq-option';
            const inputType = sectionKey === 'mcq1' ? 'radio' : 'checkbox';
            // radio groups must share the same name per question (use idx)
            const nameAttr = sectionKey === 'mcq1' ? `q_${sectionKey}_${idx}` : `q_${sectionKey}_${idx}_${i}`;
            label.innerHTML = `<input type="${inputType}" name="${nameAttr}" class="user-answer" value="${i}" data-answer="${correctKey}"> ${safePreOpt(t)}`;
            const inp = label.querySelector('input');
            if (inputType === 'radio') inp.name = `q_${sectionKey}_${idx}`;
            inp.addEventListener('change', updateNavState);
            mcqDiv.appendChild(label);
        });

        attach(mcqDiv);
    } else if (sectionKey === 'match') {
        const tbl = document.createElement('table');
        tbl.className = 'match-table';
        const left = q.left || [];
        const right = q.right || [];
        const answers = q.answer || [];

        left.forEach((L, i) => {
            const tr = document.createElement('tr');
            const tdL = document.createElement('td');
            tdL.className = 'match-left';
            tdL.innerHTML = safePre(L);

            const tdC = document.createElement('td');
            tdC.className = 'match-right';
            const sel = document.createElement('select');
            sel.className = 'user-answer';
            sel.dataset.answer = answers[i] ?? '';
            const optsHtml = ['<option value="">Select</option>'].concat(right.map(r => `<option value="${escapeForPre(r)}">${escapeForPre(r)}</option>`)).join('');
            sel.innerHTML = optsHtml;
            sel.addEventListener('change', updateNavState);
            tdC.appendChild(sel);

            const tdR = document.createElement('td');
            tdR.className = 'match-left';
            tdR.innerHTML = safePre(right[i] ?? '');

            tr.appendChild(tdL);
            tr.appendChild(tdC);
            tr.appendChild(tdR);
            tbl.appendChild(tr);
        });

        attach(tbl);
    } else if (sectionKey === 'qna' || sectionKey === 'qna1' || sectionKey === 'qna2') {

        const ta = document.createElement('textarea');
        ta.className = 'user-answer';
        ta.dataset.answer = q.answer ?? '';
        ta.addEventListener('input', updateNavState);
        attach(ta);
    }

    wrapper.appendChild(indexDiv);
    wrapper.appendChild(body);
    wrapper.appendChild(actions);
    return wrapper;
}

// Show only one section (or all if empty)
function showSection(sectionKey) {
    const blocks = document.querySelectorAll('.q-block');
    let any = false;
    blocks.forEach(b => {
        if (b.dataset.section === sectionKey) { b.style.display = 'flex'; any = true; }
        else b.style.display = 'none';
    });
    if (!any) blocks.forEach(b => b.style.display = 'flex');

    // update header text to match the section
    const meta = SECTIONS_META.find(s => s.key === sectionKey);
    setSectionHeader(meta ? meta.title : '');
}

// Update left-nav colored boxes (answered/unanswered)
function updateNavState() {
    const boxes = document.querySelectorAll('.subbox');
    boxes.forEach(box => {
        const sec = box.dataset.section;
        const idx = Number(box.dataset.index);
        const block = document.querySelector(`.q-block[data-section="${sec}"][data-index="${idx}"]`);
        if (!block) return;
        const answered = isBlockAnswered(block);
        box.classList.toggle('answered', answered);
        box.classList.toggle('unanswered', !answered);
    });
    // auto-score disabled; only grade on button click
    // updateScoreSummary();
}

function isBlockAnswered(block) {
    const inputs = Array.from(block.querySelectorAll('.user-answer'));
    if (inputs.length === 0) return false;
    return inputs.some(inp => {
        if (inp.tagName === 'SELECT' || inp.tagName === 'TEXTAREA' || inp.type === 'text') return String(inp.value).trim() !== '';
        if (inp.type === 'radio') {
            const radios = Array.from(block.querySelectorAll('input[type=radio]'));
            return radios.some(r => r.checked);
        }
        if (inp.type === 'checkbox') {
            const cbs = Array.from(block.querySelectorAll('input[type=checkbox]'));
            return cbs.some(c => c.checked);
        }
        return false;
    });
}

// ================== Scoring =====================
function gradeExamDetailed() {
    let score = 0, total = 0;
    const blocks = document.querySelectorAll('.q-block');
    blocks.forEach(block => {
        const sec = block.dataset.section;
        if (sec === 'fill') {
            block.querySelectorAll('input.user-answer').forEach(inp => {
                total += 1;
                const expected = (inp.dataset.answer || '').trim().toLowerCase();
                const val = (inp.value || '').trim().toLowerCase();
                if (val !== '' && val === expected) score += 1;
            });
        } else if (sec === 'tf') {
            block.querySelectorAll('select.user-answer').forEach(sel => {
                total += 1;
                const expected = (sel.dataset.answer || '').trim();
                const val = sel.value || '';
                if (val !== '' && val === expected) score += 1;
            });
        } else if (sec === 'mcq1') {
            const radios = Array.from(block.querySelectorAll('input[type=radio]'));
            if (radios.length) {
                total += 1;
                const correct = radios[0].dataset.answer || '';
                const chosen = radios.find(r => r.checked);
                if (chosen && chosen.value === correct) score += 1;
            }
        } else if (sec === 'mcq2' || sec === 'mcq3') {
            const cbs = Array.from(block.querySelectorAll('input[type=checkbox]'));
            if (cbs.length) {
                const correctKey = (cbs[0].dataset.answer || '');
                const correctSet = correctKey.split(',').filter(x => x !== '');
                total += correctSet.length;
                cbs.forEach(cb => { if (cb.checked && correctSet.includes(cb.value)) score += 1; });
            }
        } else if (sec === 'match') {
            const selects = Array.from(block.querySelectorAll('select.user-answer'));
            selects.forEach(sel => {
                const expected = (sel.dataset.answer || '').trim();
                if (expected !== '') total += 1;
                const chosen = (sel.value || '').trim();
                if (chosen !== '' && chosen === expected) score += 1;
            });
        } else if (sec === 'qna' || sec === 'qna1' || sec === 'qna2') {
            block.querySelectorAll('textarea.user-answer').forEach(ta => {
                const expected = (ta.dataset.answer || '').trim().toLowerCase();
                if (expected !== '') { total += 1; const val = (ta.value || '').trim().toLowerCase(); if (val === expected) score += 1; }
            });
        }
    });
    return { score, total };
}

function updateScoreSummary() {
    const el = document.getElementById('scoreSummary');
    if (!el) return;
    const g = gradeExamDetailed();
    el.innerText = `Current (auto) Score: ${g.score} / ${g.total}`;
}

function gradeExam() {
    const res = gradeExamDetailed();
    const rBox = document.getElementById('result');
    if (rBox) {
        rBox.style.display = 'block';
        rBox.innerHTML = `<h2>Result</h2><p><strong>Score:</strong> ${res.score} / ${res.total}</p>`;
    }
    revealCorrectAnswers();
    updateNavState();
}

// reveal answers
function revealCorrectAnswers() {
    const blocks = document.querySelectorAll('.q-block');
    blocks.forEach(block => {
        const sec = block.dataset.section;
        const existing = block.querySelector('.correct-hint');
        if (existing) existing.remove();
        const hint = document.createElement('div');
        hint.className = 'correct-hint';
        hint.style.marginTop = '8px';
        hint.style.color = '#0a5';

        if (sec === 'mcq1') {
            const radios = Array.from(block.querySelectorAll('input[type=radio]'));
            const correct = radios[0] ? radios[0].dataset.answer : '';
            radios.forEach(r => { if (r.value === correct) r.parentElement.style.background = '#e6ffea'; });
            hint.textContent = 'Correct option highlighted.';
            block.appendChild(hint);
        } else if (sec === 'mcq2' || sec === 'mcq3') {
            const cbs = Array.from(block.querySelectorAll('input[type=checkbox]'));
            const correctSet = cbs[0] ? (cbs[0].dataset.answer || '').split(',').filter(x => x !== '') : [];
            cbs.forEach(cb => { if (correctSet.includes(cb.value)) cb.parentElement.style.background = '#e6ffea'; });
            hint.textContent = 'Correct options highlighted.';
            block.appendChild(hint);
        } else if (sec === 'match') {
            const selects = Array.from(block.querySelectorAll('select.user-answer'));
            if (selects.length) {
                let msg = 'Correct pairs: ';
                msg += selects.map(sel => {
                    const left = sel.closest('tr').querySelector('td:first-child').innerText.trim();
                    const c = sel.dataset.answer || '';
                    return `${left} → ${c}`;
                }).join('; ');
                hint.innerHTML = msg;
                block.appendChild(hint);
            }
        } else if (sec === 'fill' || sec === 'tf') {
            const inp = block.querySelector('.user-answer');
            if (inp) {
                const ans = inp.dataset.answer || '';
                hint.textContent = 'Correct: ' + ans;
                block.appendChild(hint);
            }
        }
    });
}

// helper to infer type if data-type absent
function inferBlockType(block) {
    if (block.querySelector('input[type=radio]')) return 'mcq1';
    if (block.querySelector('input[type=checkbox]')) return 'mcq2';
    if (block.querySelector('table.match-table')) return 'match';
    if (block.querySelector('select')) return 'tf';
    if (block.querySelector('textarea')) return block.dataset.section;
    return 'fill';
}

function escapeForPreInline(s) { return escapeForPre(s); } // alias

// DOM-ready initialization to avoid "null" errors
document.addEventListener('DOMContentLoaded', () => {
    // hide result initially (fix green bar)
    const rBoxEl = document.getElementById('result');
    if (rBoxEl) rBoxEl.style.display = 'none';

    // Hook buttons
    const generateBtn = document.getElementById('generateBtn');
    const submitBtn = document.getElementById('submitBtn');
    const showAnswerBtn = document.getElementById('showAnswerBtn');

    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const paper = await buildPaper();
            renderPaper(paper);
            const r = document.getElementById('result');
            if (r) r.style.display = 'none';
        });
    }

    if (submitBtn) submitBtn.addEventListener('click', () => gradeExam());
    if (showAnswerBtn) showAnswerBtn.addEventListener('click', () => revealCorrectAnswers());

    // generate initial paper on load
    (async () => {
        try {
            const paper = await buildPaper();
            renderPaper(paper);
        } catch (err) {
            console.error('Failed to build initial paper:', err);
        }
    })();
});
