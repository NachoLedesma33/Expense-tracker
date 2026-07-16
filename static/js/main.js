(function() {
  var modal = document.getElementById('transaction-modal');

  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === this) this.classList.add('hidden');
    });
  }

  document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.target && evt.detail.target.id === 'modal-content') {
      if (evt.detail.successful && (evt.detail.xhr.status === 200 || evt.detail.xhr.status === 201)) {
        var m = document.getElementById('transaction-modal');
        if (m && !evt.detail.xhr.response) m.classList.add('hidden');
      }
    }
  });

  document.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.target && evt.detail.target.id === 'modal-content' && !evt.detail.xhr.response) {
      document.getElementById('transaction-modal')?.classList.add('hidden');
    }
  });

  document.addEventListener('click', function(e) {
    var btn = e.target.closest('.accept-category');
    if (btn) {
      e.preventDefault();
      var catId = btn.getAttribute('data-category-id');
      var textInput = document.querySelector('[name="title"]');
      var select = document.getElementById('id_category');
      if (select && catId) {
        for (var i = 0; i < select.options.length; i++) {
          if (select.options[i].value === catId) {
            select.value = catId;
            break;
          }
        }
      }
      var el = document.getElementById('suggested-category');
      if (el) el.innerHTML = '';
      if (catId && textInput && textInput.value.trim().length >= 2) {
        fetch('/transactions/learn-category/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value},
          body: JSON.stringify({text: textInput.value.trim(), category_id: parseInt(catId, 10)})
        }).catch(function() {});
      }
    }
  });
})();
