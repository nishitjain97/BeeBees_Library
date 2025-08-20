const form = document.getElementById('book-form');
const msg = document.getElementById('msg');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  msg.textContent = 'Saving…';
  try {
    const res = await fetch('/api/books', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (res.ok) {
      const book = await res.json();
      msg.textContent = `✅ Saved: ${book.title} by ${book.author_last}, ${book.author_first}`;
      form.reset();
    } else {
      const j = await res.json();
      msg.textContent = `⚠️ ${j.detail || 'Error'}`;
    }
  } catch {
    msg.textContent = '❌ Network error';
  }
});
