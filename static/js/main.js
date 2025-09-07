document.addEventListener('DOMContentLoaded', function() {
  const btn = document.getElementById('menuToggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const nav = document.querySelector('.main-nav');
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      if (nav) nav.classList.toggle('open');
    });
  }
});
