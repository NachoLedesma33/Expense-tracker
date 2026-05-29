(function() {
  const modal = document.getElementById('transaction-modal');

  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === this) this.classList.add('hidden');
    });
  }

  document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.target && evt.detail.target.id === 'modal-content') {
      if (evt.detail.successful && (evt.detail.xhr.status === 200 || evt.detail.xhr.status === 201)) {
        const m = document.getElementById('transaction-modal');
        if (m && !evt.detail.xhr.response) m.classList.add('hidden');
      }
    }
  });

  document.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.target && evt.detail.target.id === 'modal-content' && !evt.detail.xhr.response) {
      document.getElementById('transaction-modal')?.classList.add('hidden');
    }
  });
})();
