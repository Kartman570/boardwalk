const token = document.querySelector('[name=csrfmiddlewaretoken]').value;
async function send(path, data) {
  const notice = document.querySelector('#notice');
  try {
    const response = await fetch(path, {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': token},
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      notice.textContent = body.error || 'Request failed. Sign in again or reload the board.';
      return;
    }
    window.location.reload();
  } catch (error) {
    notice.textContent = 'Could not reach the server. Your change was not confirmed.';
  }
}
document.querySelectorAll('.new-card').forEach(form => form.addEventListener('submit', event => {
  event.preventDefault();
  send(`/api/columns/${form.dataset.column}/cards/`, {
    title: form.elements.title.value, description: form.elements.description.value
  });
}));
document.querySelectorAll('.card').forEach(card => {
  const id = card.dataset.id;
  const revision = Number(card.dataset.revision);
  card.querySelector('.move')?.addEventListener('click', () => send(`/api/cards/${id}/move/`, {
    column_id: Number(card.querySelector('.destination').value), position: 0, revision
  }));
  card.querySelector('.archive')?.addEventListener('click', () => send(`/api/cards/${id}/`, {
    archived: true, revision
  }));
  card.querySelector('.comment')?.addEventListener('submit', event => {
    event.preventDefault();
    send(`/api/cards/${id}/comments/`, {body: event.target.elements.body.value});
  });
});
