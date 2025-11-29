const tbody = document.querySelector('#tbl tbody');
const empty = document.getElementById('empty');
const q = document.getElementById('q');
const author = document.getElementById('author');
const yf = document.getElementById('yf');
const yt = document.getElementById('yt');
const sort = document.getElementById('sort');
const btnSearch = document.getElementById('search');
const btnClear = document.getElementById('clear');
const prev = document.getElementById('prev');
const next = document.getElementById('next');
const pageinfo = document.getElementById('pageinfo');
const pagesize = document.getElementById('pagesize');
const count = document.getElementById('count');

let page = 1;
let total = 0;

function params() {
  const ps = Number(pagesize.value || 20);
  const p = new URLSearchParams({
    page: String(page),
    page_size: String(ps),
    sort: sort.value || 'title_asc'
  });
  if (q.value.trim()) p.set('q', q.value.trim());
  if (author.value.trim()) p.set('author', author.value.trim());
  if (yf.value.trim()) p.set('year_from', yf.value.trim());
  if (yt.value.trim()) p.set('year_to', yt.value.trim());
  return p;
}

async function load() {
  const res = await fetch('/api/books?' + params().toString());
  const data = await res.json();
  render(data);
}

function render(data) {
  total = data.total;
  const container = document.getElementById("books-container");
  container.innerHTML = "";

  if (!data.items.length) {
    empty.style.display = 'block';
    count.textContent = '0 results';
  } else {
    empty.style.display = 'none';

    for (const b of data.items) {
      const div = document.createElement("div");
      div.className = "book-card";

      const coverUrl =
        `https://covers.openlibrary.org/b/isbn/${escapeHtml(b.isbn)}-M.jpg?default=true`;

      div.innerHTML = `
        <img src="${coverUrl}" onerror="this.src='/static/no-cover.png'">

        <div class="title">${escapeHtml(b.title)}</div>
        <div class="author">${escapeHtml(b.author_first)} ${escapeHtml(b.author_last)}</div>

        <div class="meta">
            Year: ${escapeHtml(b.year || "N/A")}<br>
            ISBN: ${escapeHtml(b.isbn || "N/A")}
        </div>
      `;

      if (window.LOGGED_IN === true || window.LOGGED_IN === "true") {
        div.innerHTML += `
          <button class="btn small" onclick="editBook(${b.id})">Edit</button>
          <button class="btn small danger" onclick="deleteBook(${b.id})">Delete</button>
        `;
      }

      container.appendChild(div);
    }

    count.textContent = `${data.total} result${data.total === 1 ? '' : 's'}`;
  }

  pageinfo.textContent = `Page ${data.page} of ${Math.max(1, Math.ceil(data.total / data.page_size))}`;
  prev.disabled = data.page <= 1;
  next.disabled = data.page >= Math.ceil(data.total / data.page_size);
}



function escapeHtml(s) {
  return (s ?? '').toString().replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
}

let t;
function debouncedLoad() {
  clearTimeout(t);
  t = setTimeout(() => { page = 1; load(); }, 250);
}

btnSearch.addEventListener('click', () => { page = 1; load(); });
btnClear.addEventListener('click', () => { q.value=''; author.value=''; yf.value=''; yt.value=''; page=1; load(); });
[q, author, yf, yt].forEach(el => el.addEventListener('input', debouncedLoad));
sort.addEventListener('change', () => { page = 1; load(); });
pagesize.addEventListener('change', () => { page = 1; load(); });
prev.addEventListener('click', () => { if (page>1) { page--; load(); } });
next.addEventListener('click', () => { page++; load(); });

load();
