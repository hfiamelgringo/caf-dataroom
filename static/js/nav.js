document.addEventListener('DOMContentLoaded', function () {
  const nav = document.getElementById('site-nav');

  window.addEventListener('scroll', function () {
    if (window.scrollY > 10) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  });

  // Country card carousels
  document.querySelectorAll('.carousel').forEach(function (card) {
    const slides = card.querySelectorAll('.carousel__slide');
    const dots = card.querySelectorAll('.carousel__dot');
    if (slides.length < 2) return;

    let current = 0;
    setInterval(function () {
      slides[current].classList.remove('carousel__slide--active');
      dots[current].classList.remove('carousel__dot--active');
      current = (current + 1) % slides.length;
      slides[current].classList.add('carousel__slide--active');
      dots[current].classList.add('carousel__dot--active');
    }, 3500);
  });
});
