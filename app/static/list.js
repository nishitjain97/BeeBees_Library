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

/* =========================================
   Cover resolution (Google → OpenLibrary)
   ========================================= */

const coverCache = new Map();

async function getGoogleBooksCover(isbn) {
  try {
    const res = await fetch(
      `https://www.googleapis.com/books/v1/volumes?q=isbn:${encodeURIComponent(isbn)}`
    );
    const data = await res.json();

    const thumb =
      data.items?.[0]?.volumeInfo?.imageLinks?.thumbnail ||
      data.items?.[0]?.volumeInfo?.imageLinks?.smallThumbnail ||
      null;

    if (thumb) {
      return thumb
        .replace('http://', 'https://')
        .replace('&edge=curl', '')
        .replace('zoom=1', 'zoom=2');
    }
  } catch (e) {
    console.warn('Google Books failed for ISBN', isbn);
  }
  return null;
}

async function getOpenLibraryCover(isbn) {
  try {
    const metaUrl = `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(isbn)}.json`;
    const res = await fetch(metaUrl);

    // Cover does not exist → Open Library returns 404
    if (!res.ok) return null;

    const data = await res.json();

    // Extra safety: ensure this is a valid, uploaded cover
    if (data.deleted || data.failed || !data.uploaded) {
      return null;
    }

    // If metadata exists, the image URL is guaranteed to exist
    return `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(isbn)}-M.jpg`;
  } catch (e) {
    console.warn("Open Library cover check failed for ISBN", isbn);
    return null;
  }
}

async function resolveCover(isbn) {
  if (!isbn) return null;

  if (coverCache.has(isbn)) {
    return coverCache.get(isbn);
  }

  // 1️⃣ Open Library (validated via JSON)
  const openlib = await getOpenLibraryCover(isbn);
  if (openlib) {
    coverCache.set(isbn, openlib);
    return openlib;
  }

  // 2️⃣ Google Books fallback
  const google = await getGoogleBooksCover(isbn);
  if (google) {
    coverCache.set(isbn, google);
    return google;
  }

  return null;
}


/* =========================================
   Query helpers
   ========================================= */

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

/* =========================================
   Render
   ========================================= */

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

      const img = document.createElement("img");
      img.src = "/static/no-cover.png"; // elegant final fallback
      img.loading = "lazy";

      if (b.isbn) {
        resolveCover(b.isbn).then(url => {
          if (url) img.src = url;
        });
      }

      img.onerror = () => {
        img.src = "/static/no-cover.png";
      };

      div.appendChild(img);

      div.insertAdjacentHTML(
        "beforeend",
        `
        <div class="title">${escapeHtml(b.title)}</div>
        <div class="author">
          ${escapeHtml(b.author_first)} ${escapeHtml(b.author_last)}
        </div>
        <div class="meta">
          Year: ${escapeHtml(b.year || "N/A")}<br>
          ISBN: ${escapeHtml(b.isbn || "N/A")}
        </div>
        `
      );

      if (window.LOGGED_IN === true || window.LOGGED_IN === "true") {
        div.insertAdjacentHTML(
          "beforeend",
          `
          <div class="actions">
            <button class="btn small" onclick="editBook(${b.id})">Edit</button>
            <button class="btn small danger" onclick="deleteBook(${b.id})">Delete</button>
          </div>
          `
        );
      }

      container.appendChild(div);
    }

    count.textContent = `${data.total} result${data.total === 1 ? '' : 's'}`;
  }

  pageinfo.textContent = `Page ${data.page} of ${Math.max(
    1,
    Math.ceil(data.total / data.page_size)
  )}`;
  prev.disabled = data.page <= 1;
  next.disabled = data.page >= Math.ceil(data.total / data.page_size);
}

/* =========================================
   Utils
   ========================================= */

function escapeHtml(s) {
  return (s ?? '').toString().replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[ch]));
}

/* =========================================
   Events
   ========================================= */

let t;
function debouncedLoad() {
  clearTimeout(t);
  t = setTimeout(() => {
    page = 1;
    load();
  }, 250);
}

btnSearch.addEventListener('click', () => { page = 1; load(); });
btnClear.addEventListener('click', () => {
  q.value = '';
  author.value = '';
  yf.value = '';
  yt.value = '';
  page = 1;
  load();
});

[q, author, yf, yt].forEach(el =>
  el.addEventListener('input', debouncedLoad)
);

sort.addEventListener('change', () => { page = 1; load(); });
pagesize.addEventListener('change', () => { page = 1; load(); });

prev.addEventListener('click', () => {
  if (page > 1) {
    page--;
    load();
  }
});

next.addEventListener('click', () => {
  page++;
  load();
});

load();