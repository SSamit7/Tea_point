function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function addToCart(url, btn) {
  fetch(url, {
    method: 'GET',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
  })
    .then((res) => res.text())
    .then((count) => {
      const badge = document.getElementById('cart-badge');
      const stickyCount = document.getElementById('sticky-count');
      if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
      }
      if (stickyCount) stickyCount.textContent = count;
      const bar = document.getElementById('sticky-bar');
      if (bar) bar.style.display = count > 0 ? 'flex' : 'none';
      if (btn) {
        btn.classList.add('added');
        setTimeout(() => btn.classList.remove('added'), 300);
      }
    });
}
