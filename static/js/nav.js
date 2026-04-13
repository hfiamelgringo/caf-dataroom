document.addEventListener('DOMContentLoaded', function () {
  var nav = document.getElementById('site-nav');

  window.addEventListener('scroll', function () {
    if (window.scrollY > 10) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  });

  // Country card carousels
  document.querySelectorAll('.carousel').forEach(function (card) {
    var imgs = card.querySelectorAll('.carousel__img');
    if (imgs.length < 2) return;

    var current = 0;
    setInterval(function () {
      imgs[current].classList.remove('carousel__img--active');
      current = (current + 1) % imgs.length;
      imgs[current].classList.add('carousel__img--active');
    }, 3500);
  });
});
